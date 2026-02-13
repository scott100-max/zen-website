#!/usr/bin/env python3
"""
Email Command Daemon — polls cmd.salus-mind.com for instructions
sent via email reply, executes them with Claude Code, and emails
back the result.

Run directly:  python3 tools/email-daemon.py
Or via launchd: ~/Library/LaunchAgents/com.salus-mind.email-daemon.plist
"""

import json
import os
import subprocess
import sys
import time
import fcntl
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

WORKER_URL = "https://cmd.salus-mind.com"
AUTH_TOKEN = "salus-vault-2026"
LOCK_FILE = "/tmp/salus-email-daemon.lock"
TIMEOUT_SECONDS = 30 * 60  # 30 minutes
MAX_RESULT_CHARS = 5000
WORKING_DIR = Path(__file__).resolve().parent.parent  # salus-website/

# ---------------------------------------------------------------------------
# .env loader
# ---------------------------------------------------------------------------

def load_env():
    env_path = WORKING_DIR / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())

# ---------------------------------------------------------------------------
# Lock file (prevents concurrent runs)
# ---------------------------------------------------------------------------

def acquire_lock():
    try:
        fp = open(LOCK_FILE, "w")
        fcntl.flock(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
        fp.write(str(os.getpid()))
        fp.flush()
        return fp
    except (IOError, OSError):
        print("Another instance is running. Exiting.")
        sys.exit(0)

# ---------------------------------------------------------------------------
# Worker API
# ---------------------------------------------------------------------------

def api_get(path):
    result = subprocess.run(
        ["curl", "-s", "-X", "GET", f"{WORKER_URL}{path}",
         "-H", f"Authorization: Bearer {AUTH_TOKEN}",
         "-H", "Content-Type: application/json"],
        capture_output=True, text=True, timeout=30
    )
    return json.loads(result.stdout) if result.stdout else None

def api_put(path, data):
    subprocess.run(
        ["curl", "-s", "-X", "PUT", f"{WORKER_URL}{path}",
         "-H", f"Authorization: Bearer {AUTH_TOKEN}",
         "-H", "Content-Type: application/json",
         "-d", json.dumps(data)],
        capture_output=True, text=True, timeout=30
    )

# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------

def send_email(subject, body):
    resend_key = os.environ.get("RESEND_API_KEY")
    if not resend_key:
        print("  No RESEND_API_KEY — cannot send result email")
        return

    payload = json.dumps({
        "from": "Claude <claude@salus-mind.com>",
        "to": ["scottripley@icloud.com"],
        "reply_to": "claude@salus-mind.com",
        "subject": subject,
        "text": body,
    })

    try:
        subprocess.run(
            ["curl", "-s", "-X", "POST", "https://api.resend.com/emails",
             "-H", f"Authorization: Bearer {resend_key}",
             "-H", "Content-Type: application/json",
             "-d", payload],
            capture_output=True, check=True, timeout=30
        )
        print(f"  Result email sent: {subject}")
    except Exception as e:
        print(f"  Email send failed: {e}")

# ---------------------------------------------------------------------------
# Execute instruction
# ---------------------------------------------------------------------------

def execute_instruction(instruction, subject):
    # Unset CLAUDE_CODE env vars to allow nested invocation
    env = os.environ.copy()
    for key in list(env.keys()):
        if key.startswith("CLAUDE"):
            del env[key]

    prompt = f"[Email command — subject: {subject}]\n\n{instruction}"

    print(f"  Executing: {instruction[:80]}...")

    try:
        result = subprocess.run(
            ["claude", "-p", "--dangerously-skip-permissions", prompt],
            capture_output=True, text=True,
            timeout=TIMEOUT_SECONDS,
            cwd=str(WORKING_DIR),
            env=env,
        )
        output = result.stdout.strip()
        if result.returncode != 0 and result.stderr:
            output += f"\n\n[stderr]\n{result.stderr.strip()}"
        return True, output
    except subprocess.TimeoutExpired:
        return False, "Command timed out after 30 minutes."
    except Exception as e:
        return False, f"Execution error: {e}"

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    load_env()
    lock_fp = acquire_lock()

    try:
        print(f"[{time.strftime('%H:%M:%S')}] Polling for instructions...")
        resp = api_get("/instructions")

        if not resp or not resp.get("instruction"):
            print("  No pending instructions.")
            return

        instr = resp["instruction"]
        instr_id = instr["id"]
        subject = instr.get("subject", "(no subject)")
        instruction_text = instr["instruction"]

        print(f"  Found: {instr_id} — {subject}")

        # Mark as processing
        api_put(f"/instructions/{instr_id}/status", {"status": "processing"})

        # Execute
        success, output = execute_instruction(instruction_text, subject)

        # Truncate output
        if len(output) > MAX_RESULT_CHARS:
            output = output[:MAX_RESULT_CHARS] + "\n\n[truncated]"

        # Update status
        status = "completed" if success else "failed"
        api_put(f"/instructions/{instr_id}/status", {
            "status": status,
            "result": output[:2000],  # Store summary in R2
        })

        # Send result email
        email_subject = f"Re: {subject}" if not subject.startswith("Re:") else subject
        email_body = f"{output}\n\n---\nReply to this email with more instructions."
        send_email(email_subject, email_body)

    finally:
        # Release lock
        try:
            fcntl.flock(lock_fp, fcntl.LOCK_UN)
            lock_fp.close()
            os.unlink(LOCK_FILE)
        except:
            pass

if __name__ == "__main__":
    main()
