#!/usr/bin/env python3
"""
Label Server — persists human review verdicts from browser review pages.

Receives POST /verdict with JSON payload:
  { session, chunk, verdict, notes, text, audio_url, score, flagged }

Writes to reference/human-labels/{session}-labels.csv

Run: python3 label-server.py
Listens on http://localhost:8111
"""

import json
import csv
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

LABELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reference", "human-labels")
PORT = 8111


class LabelHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self._cors_headers()
        self.end_headers()

    def do_POST(self):
        if self.path == "/verdict":
            self._handle_verdict()
        elif self.path == "/sync":
            self._handle_sync()
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self._cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "labels_dir": LABELS_DIR}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def _handle_verdict(self):
        body = self._read_body()
        if not body:
            return

        session = body.get("session", "unknown")
        chunk = body.get("chunk")
        verdict = body.get("verdict", "")
        notes = body.get("notes", "")
        text = body.get("text", "")
        audio_url = body.get("audio_url", "")
        score = body.get("score", "")
        flagged = body.get("flagged", False)

        if chunk is None:
            self._respond(400, {"error": "missing chunk number"})
            return

        self._write_verdict(session, chunk, verdict, notes, text, audio_url, score, flagged)
        self._respond(200, {"status": "saved", "session": session, "chunk": chunk, "verdict": verdict})

    def _handle_sync(self):
        """Receive a bulk sync of all ratings from a review page."""
        body = self._read_body()
        if not body:
            return

        session = body.get("session", "unknown")
        ratings = body.get("ratings", {})
        chunks_data = body.get("chunks", [])
        comments = body.get("comments", {})

        if not ratings:
            self._respond(400, {"error": "no ratings to sync"})
            return

        # Build a lookup for chunk metadata
        chunk_meta = {}
        for c in chunks_data:
            n = str(c.get("n", c.get("chunk", "")))
            chunk_meta[n] = c

        count = 0
        for chunk_str, verdict in ratings.items():
            meta = chunk_meta.get(chunk_str, {})
            self._write_verdict(
                session=session,
                chunk=int(chunk_str),
                verdict=verdict,
                notes=comments.get(chunk_str, ""),
                text=meta.get("text", ""),
                audio_url=meta.get("audio_url", ""),
                score=meta.get("score", ""),
                flagged=meta.get("flagged", False),
            )
            count += 1

        self._respond(200, {"status": "synced", "session": session, "count": count})
        print(f"  Synced {count} verdicts for session {session}")

    def _write_verdict(self, session, chunk, verdict, notes, text, audio_url, score, flagged):
        os.makedirs(LABELS_DIR, exist_ok=True)
        safe_session = session.replace("/", "-").replace(" ", "-")
        csv_path = os.path.join(LABELS_DIR, f"{safe_session}-labels.csv")

        # Read existing data to update (not append duplicates)
        existing = {}
        if os.path.exists(csv_path):
            with open(csv_path, "r", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    existing[int(row["chunk"])] = row

        # Update or add
        existing[int(chunk)] = {
            "chunk": int(chunk),
            "session": session,
            "verdict": verdict,
            "notes": notes,
            "text": text,
            "audio_url": audio_url,
            "score": score,
            "flagged": flagged,
            "timestamp": datetime.now().isoformat(),
        }

        # Write sorted by chunk number
        fieldnames = ["chunk", "session", "verdict", "notes", "text", "audio_url", "score", "flagged", "timestamp"]
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for k in sorted(existing.keys()):
                writer.writerow(existing[k])

        print(f"  [{session}] chunk {chunk}: {verdict}" + (f" — {notes}" if notes else ""))

    def _read_body(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length)
            return json.loads(raw)
        except Exception as e:
            self._respond(400, {"error": str(e)})
            return None

    def _respond(self, code, data):
        self.send_response(code)
        self._cors_headers()
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def log_message(self, format, *args):
        # Quieter logging — only show verdicts
        if "/verdict" in str(args) or "/sync" in str(args):
            return
        super().log_message(format, *args)


if __name__ == "__main__":
    os.makedirs(LABELS_DIR, exist_ok=True)
    print(f"Label server listening on http://localhost:{PORT}")
    print(f"Labels directory: {LABELS_DIR}")
    print(f"Endpoints:")
    print(f"  POST /verdict  — save single verdict")
    print(f"  POST /sync     — bulk sync all ratings from a review page")
    print(f"  GET  /health   — server status check")
    print()
    HTTPServer(("127.0.0.1", PORT), LabelHandler).serve_forever()
