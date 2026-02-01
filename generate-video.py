import subprocess
import os
import json
import tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont

BASE = "/Users/scottripley/salus-website"

# Video definitions: (audio, title, subtitle, background_clip, output)
videos = [
    (
        "content/audio/01-morning-meditation.mp3",
        "10-Minute\nMorning Meditation",
        "Start Your Day with Clarity",
        "content/video/backgrounds/morning.mp4",
        "content/video/01-morning-meditation.mp4",
    ),
    (
        "content/audio/02-deep-sleep.mp3",
        "Deep Sleep\nMeditation",
        "30 Minutes — Fall Asleep Peacefully",
        "content/video/backgrounds/sleep.mp4",
        "content/video/02-deep-sleep.mp4",
    ),
    (
        "content/audio/03-breathing-for-anxiety.mp3",
        "Breathing for\nAnxiety Relief",
        "Two Techniques That Work Instantly",
        "content/video/backgrounds/breathing.mp4",
        "content/video/03-breathing-for-anxiety.mp4",
    ),
    (
        "content/audio/04-science-of-mindfulness.mp3",
        "The Science of\nMindfulness",
        "How Meditation Changes Your Brain",
        "content/video/backgrounds/science.mp4",
        "content/video/04-science-of-mindfulness.mp4",
    ),
]

LOGO = os.path.join(BASE, "Salus.PNG")


def get_duration(path):
    """Get duration of a media file in seconds."""
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", path],
        capture_output=True, text=True,
    )
    info = json.loads(result.stdout)
    return float(info["format"]["duration"])


def create_title_overlay(title, subtitle, output_path, width=1920, height=1080):
    """Create a transparent PNG overlay with title, subtitle, and branding."""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    try:
        title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 72)
        subtitle_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 36)
        brand_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 28)
    except (OSError, IOError):
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
        brand_font = ImageFont.load_default()

    # Title — centered with shadow
    title_bbox = draw.multiline_textbbox((0, 0), title, font=title_font, align="center")
    title_w = title_bbox[2] - title_bbox[0]
    title_h = title_bbox[3] - title_bbox[1]
    title_x = (width - title_w) // 2
    title_y = (height - title_h) // 2 - 50

    # Shadow (stronger for readability over video)
    for dx, dy in [(0,2),(2,0),(2,2),(0,-2),(-2,0)]:
        draw.multiline_text((title_x + dx, title_y + dy), title,
                            fill=(0, 0, 0, 160), font=title_font, align="center")
    draw.multiline_text((title_x, title_y), title,
                        fill=(255, 255, 255, 255), font=title_font, align="center")

    # Subtitle
    sub_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
    sub_w = sub_bbox[2] - sub_bbox[0]
    sub_x = (width - sub_w) // 2
    sub_y = title_y + title_h + 30

    for dx, dy in [(0,2),(2,0),(2,2)]:
        draw.text((sub_x + dx, sub_y + dy), subtitle,
                  fill=(0, 0, 0, 120), font=subtitle_font)
    draw.text((sub_x, sub_y), subtitle,
              fill=(255, 255, 255, 220), font=subtitle_font)

    # SALUS brand bottom-right
    brand_text = "SALUS"
    brand_bbox = draw.textbbox((0, 0), brand_text, font=brand_font)
    brand_w = brand_bbox[2] - brand_bbox[0]
    draw.text((width - brand_w - 40, height - 60), brand_text,
              fill=(255, 255, 255, 150), font=brand_font)

    # Logo
    try:
        logo = Image.open(LOGO).convert("RGBA")
        logo_h = 48
        logo_w = int(logo.width * (logo_h / logo.height))
        logo = logo.resize((logo_w, logo_h), Image.LANCZOS)
        logo_x = width - brand_w - logo_w - 56
        logo_y = height - logo_h - 42
        alpha = logo.split()[3].point(lambda p: int(p * 0.6))
        logo.putalpha(alpha)
        img.paste(logo, (logo_x, logo_y), logo)
    except Exception:
        pass

    img.save(output_path, "PNG")


def build_video(audio_rel, title, subtitle, bg_rel, output_rel):
    audio_path = os.path.join(BASE, audio_rel)
    bg_path = os.path.join(BASE, bg_rel)
    output_path = os.path.join(BASE, output_rel)
    thumb_path = output_path.replace(".mp4", "-thumb.jpg")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    if not os.path.exists(audio_path):
        print(f"  SKIP: Audio not found: {audio_path}")
        return
    if not os.path.exists(bg_path):
        print(f"  SKIP: Background not found: {bg_path}")
        return

    duration = get_duration(audio_path)
    print(f"  Audio duration: {duration:.1f}s")

    with tempfile.TemporaryDirectory() as tmpdir:
        overlay_path = os.path.join(tmpdir, "overlay.png")

        print(f"  Creating title overlay...")
        create_title_overlay(title, subtitle, overlay_path)

        # FFmpeg filter:
        # - Loop background video to match audio duration
        # - Add dark overlay for text readability
        # - Overlay title PNG with fade-in
        # - Fade in/out on the composite
        # - Fade out audio at the end

        filter_complex = (
            # Loop and scale background video to 1920x1080, match audio duration
            f"[0:v]loop=-1:size=32767,setpts=N/30/TB,"
            f"scale=1920:1080:force_original_aspect_ratio=increase,"
            f"crop=1920:1080,setsar=1[bgraw];"
            # Dark overlay for text readability
            f"[bgraw]colorbalance=bs=-0.1:gs=-0.1:rs=-0.1,"
            f"eq=brightness=-0.15:saturation=0.85[bg];"
            # Title overlay — fade in from 1s over 2s
            f"[1:v]format=rgba,fade=t=in:st=1:d=2:alpha=1[title];"
            # Composite bg + title
            f"[bg][title]overlay=0:0:shortest=1[composited];"
            # Video fade in/out
            f"[composited]fade=t=in:st=0:d=2,fade=t=out:st={duration - 3}:d=3[vout];"
            # Audio fade out last 3s
            f"[2:a]afade=t=out:st={duration - 3}:d=3[aout]"
        )

        cmd = [
            "ffmpeg", "-y",
            "-stream_loop", "-1", "-i", bg_path,      # 0: looped background video
            "-loop", "1", "-i", overlay_path,           # 1: title overlay PNG
            "-i", audio_path,                           # 2: audio
            "-filter_complex", filter_complex,
            "-map", "[vout]", "-map", "[aout]",
            "-c:v", "libx264", "-preset", "medium", "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart",
            "-t", str(duration),
            output_path,
        ]

        print(f"  Running FFmpeg...")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"  ERROR: {result.stderr[-1000:]}")
            return

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"  Saved: {output_path} ({size_mb:.1f} MB)")

    # Generate thumbnail at 4 seconds (after title has faded in)
    subprocess.run([
        "ffmpeg", "-y", "-i", output_path,
        "-ss", "4", "-vframes", "1", "-vf", "scale=1280:720",
        thumb_path,
    ], capture_output=True, text=True)

    if os.path.exists(thumb_path):
        print(f"  Thumbnail: {thumb_path}")


if __name__ == "__main__":
    print("=== Salus Video Generator ===\n")

    for audio_rel, title, subtitle, bg_rel, output_rel in videos:
        print(f"Generating: {title.replace(chr(10), ' ')}")
        build_video(audio_rel, title, subtitle, bg_rel, output_rel)
        print()

    print("Done!")
