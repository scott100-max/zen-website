#!/usr/bin/env python3
"""Build multiple variations with different settings."""

import subprocess
import shutil
from pathlib import Path

ONEDRIVE = Path.home() / "Library/CloudStorage/OneDrive-Personal/Salus-Samples"
AUDIO_DIR = Path("content/audio")

# Variations to build
VARIATIONS = [
    {"name": "1-baseline", "ambient_db": -14, "temp": 0.3},
    {"name": "2-louder-ambient", "ambient_db": -12, "temp": 0.3},
    {"name": "3-quieter-ambient", "ambient_db": -16, "temp": 0.3},
    {"name": "4-warmer-voice", "ambient_db": -14, "temp": 0.4},
    {"name": "5-warmest-voice", "ambient_db": -14, "temp": 0.5},
]

def update_script(ambient_db, temp):
    """Update build-session-v3.py with new settings."""
    script = Path("build-session-v3.py").read_text()

    # Update ambient volume
    import re
    script = re.sub(
        r'AMBIENT_VOLUME_DB = -?\d+',
        f'AMBIENT_VOLUME_DB = {ambient_db}',
        script
    )

    # Update temperature
    script = re.sub(
        r'"temperature": [\d.]+',
        f'"temperature": {temp}',
        script
    )

    Path("build-session-v3.py").write_text(script)

def main():
    session = "09-rainfall-sleep-journey"

    for var in VARIATIONS:
        print(f"\n{'='*60}")
        print(f"Building variation: {var['name']}")
        print(f"  Ambient: {var['ambient_db']}dB, Temp: {var['temp']}")
        print(f"{'='*60}\n")

        # Update settings
        update_script(var['ambient_db'], var['temp'])

        # Run build
        result = subprocess.run(
            ["python3", "build-session-v3.py", session],
            capture_output=False
        )

        if result.returncode == 0:
            # Copy to OneDrive with variation name
            src = AUDIO_DIR / f"{session}.mp3"
            dst = ONEDRIVE / f"rainfall-{var['name']}.mp3"
            shutil.copy(src, dst)
            print(f"\n  Copied to: {dst}")
        else:
            print(f"\n  FAILED: {var['name']}")

    # Restore baseline settings
    update_script(-14, 0.3)
    print("\n\nAll variations complete!")

if __name__ == "__main__":
    main()
