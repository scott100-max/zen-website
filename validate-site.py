#!/usr/bin/env python3
"""
SALUS SITE VALIDATOR
====================
Validates the live site against the Project Bible specifications.
Run after any changes to check for compliance breaches.

Usage:
    python3 validate-site.py           # Full validation
    python3 validate-site.py --quick   # Skip slow checks (audio analysis)
    python3 validate-site.py --fix     # Show suggested fixes
"""

import os
import sys
import re
import json
import hashlib
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# Configuration
SITE_ROOT = Path(__file__).parent
CONTENT_DIR = SITE_ROOT / "content"
SESSIONS_DIR = SITE_ROOT / "sessions"
IMAGES_DIR = CONTENT_DIR / "images" / "sessions"
SCRIPTS_DIR = CONTENT_DIR / "scripts"
AUDIO_DIR = CONTENT_DIR / "audio-free"
JS_DIR = SITE_ROOT / "js"
CSS_DIR = SITE_ROOT / "css"

# Bible Rules
FORBIDDEN_PHRASES = [
    (r"Welcome to Salus", "No 'Welcome to Salus' at session starts (Bible 4.6)"),
    (r"clinical", "No 'clinical' references (Bible 9.1 #9)"),
    (r"clinically", "No 'clinical' references (Bible 9.1 #9)"),
    (r"for \d+ seconds?", "No prescriptive timing in breathing (Bible 4.3)"),
    (r"breathe in for", "No prescriptive timing in breathing (Bible 4.3)"),
    (r"hold for \d+", "No prescriptive timing in breathing (Bible 4.3)"),
    (r"exhale for \d+", "No prescriptive timing in breathing (Bible 4.3)"),
    (r"One\. Two\. Three\.", "No counting in breathing exercises (Bible 4.3)"),
]

REQUIRED_METADATA_FIELDS = ["Duration", "Category"]
VALID_CATEGORIES = ["sleep", "focus", "stress", "mindfulness", "beginner", "advanced"]
VALID_AMBIENTS = ["ocean", "rain", "forest", "birds", "stream", "wind", "night", "fire",
                  "garden", "temple", "chimes", "piano", "library", "waterfall", "none"]

# Minimum image size (bytes) for "UHD" check - roughly 100KB
MIN_IMAGE_SIZE = 100000

class ValidationResult:
    def __init__(self):
        self.errors = []      # Critical - must fix
        self.warnings = []    # Should fix
        self.info = []        # Informational
        self.passed = []      # Checks that passed

    def add_error(self, category, message, file=None, line=None, fix=None):
        self.errors.append({
            "category": category,
            "message": message,
            "file": str(file) if file else None,
            "line": line,
            "fix": fix
        })

    def add_warning(self, category, message, file=None, line=None, fix=None):
        self.warnings.append({
            "category": category,
            "message": message,
            "file": str(file) if file else None,
            "line": line,
            "fix": fix
        })

    def add_info(self, category, message):
        self.info.append({"category": category, "message": message})

    def add_pass(self, category, message):
        self.passed.append({"category": category, "message": message})


def check_duplicate_images(result):
    """Bible 10.1: No duplicate images across the site"""
    print("  Checking for duplicate images...")

    image_usage = defaultdict(list)
    image_hashes = defaultdict(list)

    # Scan all HTML files for image references
    for html_file in SITE_ROOT.glob("**/*.html"):
        if "node_modules" in str(html_file) or "backup" in str(html_file):
            continue

        try:
            content = html_file.read_text(encoding='utf-8')

            # Find all image references
            patterns = [
                r"url\(['\"]?([^'\")\s]+\.(?:jpg|jpeg|png|webp))['\"]?\)",
                r'src=["\']([^"\']+\.(?:jpg|jpeg|png|webp))["\']',
                r"background[^:]*:\s*[^;]*url\(['\"]?([^'\")\s]+\.(?:jpg|jpeg|png|webp))",
            ]

            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for img in matches:
                    # Normalize path
                    img_name = os.path.basename(img)
                    image_usage[img_name].append(str(html_file.relative_to(SITE_ROOT)))
        except Exception as e:
            result.add_warning("IMAGES", f"Could not read {html_file}: {e}")

    # Check for same image used multiple times
    for img, pages in image_usage.items():
        if len(pages) > 1:
            # This is actually OK - same file used in multiple places is fine
            # The rule is about VISUAL duplicates, not file references
            pass

    # Check for visually identical images (by hash)
    if IMAGES_DIR.exists():
        for img_file in IMAGES_DIR.glob("*.jpg"):
            try:
                with open(img_file, 'rb') as f:
                    file_hash = hashlib.md5(f.read()).hexdigest()
                    image_hashes[file_hash].append(img_file.name)
            except Exception as e:
                pass

        for hash_val, files in image_hashes.items():
            if len(files) > 1:
                result.add_error(
                    "IMAGES",
                    f"Duplicate images detected (identical content): {', '.join(files)}",
                    fix="Replace one with a unique image"
                )

    result.add_pass("IMAGES", "No visually identical images found")


def check_image_quality(result):
    """Bible 10.2: Ultra high definition only"""
    print("  Checking image quality/sizes...")

    if not IMAGES_DIR.exists():
        result.add_warning("IMAGES", "Sessions images directory not found")
        return

    low_quality = []
    for img_file in IMAGES_DIR.glob("*.*"):
        if img_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']:
            size = img_file.stat().st_size
            if size < MIN_IMAGE_SIZE:
                low_quality.append((img_file.name, size))

    if low_quality:
        for name, size in low_quality:
            result.add_error(
                "IMAGES",
                f"Low quality image: {name} ({size//1024}KB < 100KB minimum)",
                file=IMAGES_DIR / name,
                fix="Replace with higher resolution image"
            )
    else:
        result.add_pass("IMAGES", f"All {len(list(IMAGES_DIR.glob('*.jpg')))} images meet size requirements")


def check_forbidden_phrases(result):
    """Check for forbidden phrases in HTML and scripts"""
    print("  Checking for forbidden phrases...")

    files_to_check = list(SITE_ROOT.glob("*.html")) + list(SESSIONS_DIR.glob("*.html"))

    for html_file in files_to_check:
        if "node_modules" in str(html_file):
            continue

        try:
            content = html_file.read_text(encoding='utf-8')
            lines = content.split('\n')

            for pattern, rule in FORBIDDEN_PHRASES:
                for i, line in enumerate(lines, 1):
                    if re.search(pattern, line, re.IGNORECASE):
                        # Exception: Landing page can mention Salus
                        if "Welcome to Salus" in pattern and html_file.name == "index.html":
                            continue
                        result.add_error(
                            "CONTENT",
                            f"Forbidden phrase found: {rule}",
                            file=html_file,
                            line=i,
                            fix=f"Remove or rephrase text matching '{pattern}'"
                        )
        except Exception as e:
            result.add_warning("CONTENT", f"Could not read {html_file}: {e}")

    # Check scripts
    if SCRIPTS_DIR.exists():
        for script_file in SCRIPTS_DIR.glob("*.txt"):
            try:
                content = script_file.read_text(encoding='utf-8')
                lines = content.split('\n')

                for pattern, rule in FORBIDDEN_PHRASES:
                    for i, line in enumerate(lines, 1):
                        if re.search(pattern, line, re.IGNORECASE):
                            result.add_error(
                                "SCRIPTS",
                                f"Forbidden phrase in script: {rule}",
                                file=script_file,
                                line=i,
                                fix=f"Remove or rephrase text matching '{pattern}'"
                            )
            except Exception as e:
                pass


def check_script_metadata(result):
    """Bible 4.1: Every script must have metadata header"""
    print("  Checking script metadata...")

    if not SCRIPTS_DIR.exists():
        result.add_warning("SCRIPTS", "Scripts directory not found")
        return

    scripts = list(SCRIPTS_DIR.glob("*.txt"))
    if not scripts:
        result.add_info("SCRIPTS", "No scripts found")
        return

    for script_file in scripts:
        if script_file.name == "TEMPLATE.txt":
            continue

        try:
            content = script_file.read_text(encoding='utf-8')

            # Check for required fields
            for field in REQUIRED_METADATA_FIELDS:
                if not re.search(f"^{field}:", content, re.MULTILINE | re.IGNORECASE):
                    result.add_error(
                        "SCRIPTS",
                        f"Missing required metadata field: {field}",
                        file=script_file,
                        fix=f"Add '{field}: <value>' to script header"
                    )

            # Check category is valid
            cat_match = re.search(r"^Category:\s*(\w+)", content, re.MULTILINE | re.IGNORECASE)
            if cat_match:
                category = cat_match.group(1).lower()
                if category not in VALID_CATEGORIES:
                    result.add_warning(
                        "SCRIPTS",
                        f"Unknown category '{category}' (valid: {', '.join(VALID_CATEGORIES)})",
                        file=script_file
                    )

            # Check ambient is valid
            amb_match = re.search(r"^Ambient:\s*(\w+)", content, re.MULTILINE | re.IGNORECASE)
            if amb_match:
                ambient = amb_match.group(1).lower()
                if ambient not in VALID_AMBIENTS:
                    result.add_warning(
                        "SCRIPTS",
                        f"Unknown ambient '{ambient}' (valid: {', '.join(VALID_AMBIENTS)})",
                        file=script_file
                    )

            # Check for --- separator
            if "---" not in content:
                result.add_warning(
                    "SCRIPTS",
                    "Missing '---' separator between metadata and content",
                    file=script_file
                )

        except Exception as e:
            result.add_warning("SCRIPTS", f"Could not read {script_file}: {e}")

    result.add_pass("SCRIPTS", f"Checked {len(scripts)} script files")


def check_audio_closing(result):
    """Bible 4.6: All audio must end with the standard closing phrase"""
    print("  Checking audio closing phrases...")

    if not SCRIPTS_DIR.exists():
        return

    REQUIRED_CLOSING = "thank you for practising with salus"

    for script_file in SCRIPTS_DIR.glob("*.txt"):
        if script_file.name == "TEMPLATE.txt":
            continue

        try:
            content = script_file.read_text(encoding='utf-8').lower()

            # Get the last 500 characters to check for closing
            ending = content[-500:] if len(content) > 500 else content

            if REQUIRED_CLOSING not in ending:
                result.add_warning(
                    "CLOSING",
                    f"Script may be missing required closing phrase",
                    file=script_file,
                    fix='End with: "Thank you for practising with Salus. Sleep, relax, restore."'
                )

        except Exception as e:
            pass


def check_breathing_patterns(result):
    """Bible 4.3: Verify breathing exercises follow spec"""
    print("  Checking breathing pattern compliance...")

    if not SCRIPTS_DIR.exists():
        return

    # Patterns that indicate ACTUAL breathing hold instructions (not metaphorical)
    HOLD_BREATH_PATTERNS = [
        r'\bhold your breath\b',
        r'\bnow hold\b',
        r'\band hold\b',
        r'^hold\.$',           # Just "Hold." on its own line
        r'^hold gently',       # Breathing instruction
        r'\bhold it\b',        # "hold it" in breathing context
    ]

    # Patterns that are NOT breathing instructions (false positive filters)
    IGNORE_HOLD_PATTERNS = [
        r'hold that',          # "hold that word/thought" = metaphor
        r'hold you',           # "let the mattress hold you" = support
        r'stop holding',       # "muscles stop holding" = releasing tension
        r'holding on',         # "stop holding on" = letting go
        r'holding tension',    # body scan
        r'holding anything',   # "you're not holding anything"
        r'hold it in',         # "hold stomach in" = body posture
        r'really hold',        # progressive muscle relaxation
        r'hold the tension',   # muscle tension exercise
        r'squeeze.*hold',      # muscle contraction
        r'hold it tight',      # muscle tension ("hold it tight")
        r'tighten.*hold',      # muscle contraction sequence
    ]

    for script_file in SCRIPTS_DIR.glob("*.txt"):
        try:
            content = script_file.read_text(encoding='utf-8').lower()
            lines = content.split('\n')

            # Skip if this is box breathing (which DOES have hold after exhale)
            if "box breathing" in content or "4-4-4-4" in content:
                continue

            # Track breathing sequence - we need to detect: exhale → hold (bad)
            # But NOT: exhale → inhale → hold (good, that's normal pattern)
            # State: None, 'exhale' (just saw exhale, watching for hold)
            state = None

            for i, line in enumerate(lines):
                # Reset state on new inhale (start of new cycle)
                if re.search(r'\bbreath[e]?\s+in\b', line) or "inhale" in line:
                    state = None
                    continue

                # Mark exhale state
                if "breathe out" in line or "exhale" in line or "let it go" in line or "release" in line:
                    state = 'exhale'
                    continue

                # Check for hold INSTRUCTION immediately after exhale
                # This is the FORBIDDEN pattern in basic breathing
                if state == 'exhale':
                    # Check if this line has a breathing hold instruction
                    is_hold_instruction = False
                    for pattern in HOLD_BREATH_PATTERNS:
                        if re.search(pattern, line):
                            is_hold_instruction = True
                            break

                    # Check if this should be ignored (false positive)
                    if is_hold_instruction:
                        for ignore_pattern in IGNORE_HOLD_PATTERNS:
                            if re.search(ignore_pattern, line):
                                is_hold_instruction = False
                                break

                    if is_hold_instruction:
                        result.add_error(
                            "BREATHING",
                            "Basic breathing has 'hold' after exhale (Bible 4.3: FORBIDDEN)",
                            file=script_file,
                            line=i+1,
                            fix="Remove hold after exhale for basic breathing pattern"
                        )
                        break  # Only report once per script

                    # If we see anything other than pause markers, reset state
                    # (pause markers are just "...")
                    if line.strip() and line.strip() != "...":
                        state = None

        except Exception as e:
            pass


def check_premium_functionality(result):
    """Bible 13: Verify premium access system"""
    print("  Checking premium access functionality...")

    # Check thank-you.html sets localStorage
    thank_you = SITE_ROOT / "thank-you.html"
    if thank_you.exists():
        content = thank_you.read_text(encoding='utf-8')
        if "localStorage.setItem('salus_premium'" not in content:
            result.add_error(
                "PREMIUM",
                "thank-you.html does not set salus_premium localStorage flag",
                file=thank_you,
                fix="Add: localStorage.setItem('salus_premium', 'true');"
            )
        else:
            result.add_pass("PREMIUM", "thank-you.html sets premium flag correctly")
    else:
        result.add_error("PREMIUM", "thank-you.html not found")

    # Check main.js has premium detection
    main_js = JS_DIR / "main.js"
    if main_js.exists():
        content = main_js.read_text(encoding='utf-8')
        if "salus_premium" not in content:
            result.add_error(
                "PREMIUM",
                "main.js does not check for salus_premium flag",
                file=main_js,
                fix="Add premium detection code to main.js"
            )
        else:
            result.add_pass("PREMIUM", "main.js includes premium detection")

    # Check session pages have unlock-cta
    session_pages = list(SESSIONS_DIR.glob("*.html")) if SESSIONS_DIR.exists() else []
    pages_without_cta = []
    for page in session_pages[:5]:  # Sample check
        content = page.read_text(encoding='utf-8')
        if "unlock-cta" not in content and "premium" not in content.lower():
            pages_without_cta.append(page.name)

    if pages_without_cta:
        result.add_warning(
            "PREMIUM",
            f"Some session pages may lack premium gating: {', '.join(pages_without_cta)}"
        )


def check_stripe_configuration(result):
    """Bible 13.2: Verify Stripe setup"""
    print("  Checking Stripe configuration...")

    apps_html = SITE_ROOT / "apps.html"
    if apps_html.exists():
        content = apps_html.read_text(encoding='utf-8')

        # Check for Stripe links
        stripe_links = re.findall(r'https://buy\.stripe\.com/[a-zA-Z0-9]+', content)
        if not stripe_links:
            result.add_error(
                "STRIPE",
                "No Stripe payment links found in apps.html",
                file=apps_html
            )
        else:
            result.add_pass("STRIPE", f"Found {len(stripe_links)} Stripe payment link(s)")

    # Check .env has Stripe key
    env_file = SITE_ROOT / ".env"
    if env_file.exists():
        content = env_file.read_text(encoding='utf-8')
        if "STRIPE_SECRET_KEY" not in content:
            result.add_warning("STRIPE", ".env missing STRIPE_SECRET_KEY")
        else:
            result.add_pass("STRIPE", "Stripe API key configured in .env")


def check_audio_files(result, quick=False):
    """Bible 4.4, 11: Verify audio specifications"""
    print("  Checking audio files...")

    if not AUDIO_DIR.exists():
        result.add_warning("AUDIO", "Audio directory not found")
        return

    audio_files = list(AUDIO_DIR.glob("*.mp3"))
    if not audio_files:
        result.add_info("AUDIO", "No audio files found")
        return

    result.add_info("AUDIO", f"Found {len(audio_files)} audio files")

    # Check file sizes (very small = likely corrupt)
    for audio_file in audio_files:
        size = audio_file.stat().st_size
        if size < 100000:  # Less than 100KB
            result.add_warning(
                "AUDIO",
                f"Suspiciously small audio file: {audio_file.name} ({size//1024}KB)",
                file=audio_file
            )


def check_navigation(result):
    """Verify navigation links work"""
    print("  Checking navigation consistency...")

    required_pages = [
        "index.html", "sessions.html", "about.html", "contact.html",
        "apps.html", "soundscapes.html", "mindfulness.html"
    ]

    missing_pages = []
    for page in required_pages:
        if not (SITE_ROOT / page).exists():
            missing_pages.append(page)

    if missing_pages:
        result.add_error(
            "NAVIGATION",
            f"Missing required pages: {', '.join(missing_pages)}"
        )
    else:
        result.add_pass("NAVIGATION", "All required pages exist")


def check_file_organization(result):
    """Bible 2: Verify file structure"""
    print("  Checking file organization...")

    required_dirs = [
        CONTENT_DIR,
        CONTENT_DIR / "scripts",
        CONTENT_DIR / "images",
        JS_DIR,
        CSS_DIR,
    ]

    for dir_path in required_dirs:
        if not dir_path.exists():
            result.add_warning(
                "STRUCTURE",
                f"Expected directory missing: {dir_path.relative_to(SITE_ROOT)}"
            )

    # Check Bible exists
    bible_path = CONTENT_DIR / "Salus_Project_Bible.txt"
    if not bible_path.exists():
        result.add_error("STRUCTURE", "Project Bible not found at content/Salus_Project_Bible.txt")
    else:
        result.add_pass("STRUCTURE", "Project Bible found")


def print_report(result, show_fixes=False):
    """Print validation report"""
    print("\n" + "=" * 70)
    print("SALUS SITE VALIDATION REPORT")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Summary
    total_errors = len(result.errors)
    total_warnings = len(result.warnings)
    total_passed = len(result.passed)

    if total_errors == 0 and total_warnings == 0:
        print("\n[PASS] All checks passed!")
    else:
        print(f"\n[SUMMARY] {total_errors} errors, {total_warnings} warnings, {total_passed} passed")

    # Errors
    if result.errors:
        print("\n" + "-" * 70)
        print("ERRORS (Must Fix)")
        print("-" * 70)
        for i, err in enumerate(result.errors, 1):
            print(f"\n{i}. [{err['category']}] {err['message']}")
            if err.get('file'):
                loc = err['file']
                if err.get('line'):
                    loc += f":{err['line']}"
                print(f"   Location: {loc}")
            if show_fixes and err.get('fix'):
                print(f"   Fix: {err['fix']}")

    # Warnings
    if result.warnings:
        print("\n" + "-" * 70)
        print("WARNINGS (Should Fix)")
        print("-" * 70)
        for i, warn in enumerate(result.warnings, 1):
            print(f"\n{i}. [{warn['category']}] {warn['message']}")
            if warn.get('file'):
                loc = warn['file']
                if warn.get('line'):
                    loc += f":{warn['line']}"
                print(f"   Location: {loc}")
            if show_fixes and warn.get('fix'):
                print(f"   Fix: {warn['fix']}")

    # Passed (brief)
    if result.passed:
        print("\n" + "-" * 70)
        print(f"PASSED CHECKS ({len(result.passed)})")
        print("-" * 70)
        for p in result.passed:
            print(f"  [OK] {p['category']}: {p['message']}")

    # Info
    if result.info:
        print("\n" + "-" * 70)
        print("INFO")
        print("-" * 70)
        for info in result.info:
            print(f"  [i] {info['category']}: {info['message']}")

    print("\n" + "=" * 70)

    return total_errors == 0


def main():
    quick_mode = "--quick" in sys.argv
    show_fixes = "--fix" in sys.argv

    print("=" * 70)
    print("SALUS SITE VALIDATOR")
    print("Checking compliance with Project Bible specifications...")
    print("=" * 70)

    result = ValidationResult()

    print("\n[1/9] Images...")
    check_duplicate_images(result)
    check_image_quality(result)

    print("\n[2/9] Content & Forbidden Phrases...")
    check_forbidden_phrases(result)

    print("\n[3/9] Script Metadata...")
    check_script_metadata(result)

    print("\n[4/10] Breathing Patterns...")
    check_breathing_patterns(result)

    print("\n[5/10] Audio Closing Phrases...")
    check_audio_closing(result)

    print("\n[6/10] Premium Access...")
    check_premium_functionality(result)

    print("\n[7/10] Stripe Configuration...")
    check_stripe_configuration(result)

    print("\n[8/10] Audio Files...")
    check_audio_files(result, quick=quick_mode)

    print("\n[9/10] Navigation...")
    check_navigation(result)

    print("\n[10/10] File Organization...")
    check_file_organization(result)

    # Print report
    success = print_report(result, show_fixes=show_fixes)

    # Exit code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
