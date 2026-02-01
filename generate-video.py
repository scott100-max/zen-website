import subprocess
import os
import json
import tempfile
import glob
from PIL import Image, ImageDraw, ImageFont

BASE = "/Users/scottripley/salus-website"

# Video definitions: audio, title, subtitle, clips_dir, output, keywords
videos = [
    {
        "audio": "content/audio/01-morning-meditation.mp3",
        "title": "10-Minute\nMorning Meditation",
        "subtitle": "Start Your Day with Clarity",
        "clips_dir": "content/video/backgrounds/morning",
        "output": "content/video/01-morning-meditation.mp4",
        "keywords": [
            "stillness", "clarity", "breathe", "present moment",
            "gratitude", "intention", "awareness", "peace",
        ],
    },
    {
        "audio": "content/audio/02-deep-sleep.mp3",
        "title": "Deep Sleep\nMeditation",
        "subtitle": "30 Minutes — Fall Asleep Peacefully",
        "clips_dir": "content/video/backgrounds/sleep",
        "output": "content/video/02-deep-sleep.mp4",
        "keywords": [
            "let go", "safe", "heavy", "warm",
            "floating", "deep rest", "surrender", "peace",
        ],
    },
    {
        "audio": "content/audio/03-breathing-for-anxiety.mp3",
        "title": "Breathing for\nAnxiety Relief",
        "subtitle": "Two Techniques That Work Instantly",
        "clips_dir": "content/video/backgrounds/breathing",
        "output": "content/video/03-breathing-for-anxiety.mp4",
        "keywords": [
            "breathe in", "hold", "exhale", "calm",
            "vagus nerve", "box breathing", "release", "steady",
        ],
    },
    {
        "audio": "content/audio/04-science-of-mindfulness.mp3",
        "title": "The Science of\nMindfulness",
        "subtitle": "How Meditation Changes Your Brain",
        "clips_dir": "content/video/backgrounds/science",
        "output": "content/video/04-science-of-mindfulness.mp4",
        "keywords": [
            "neuroplasticity", "amygdala", "grey matter", "focus",
            "8 weeks", "rewire", "cortisol", "presence",
        ],
    },
]

LOGO = os.path.join(BASE, "Salus.PNG")
XFADE_DUR = 2  # seconds for crossfade dissolve between clips


def get_duration(path):
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", path],
        capture_output=True, text=True,
    )
    info = json.loads(result.stdout)
    return float(info["format"]["duration"])


def create_title_overlay(title, subtitle, output_path, width=1920, height=1080):
    """Create transparent PNG with semi-transparent backdrop behind text for readability."""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    try:
        title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 96)
        subtitle_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 42)
        brand_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 28)
    except (OSError, IOError):
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
        brand_font = ImageFont.load_default()

    # Measure title
    title_bbox = draw.multiline_textbbox((0, 0), title, font=title_font, align="center")
    title_w = title_bbox[2] - title_bbox[0]
    title_h = title_bbox[3] - title_bbox[1]
    title_x = (width - title_w) // 2
    title_y = (height - title_h) // 2 - 50

    # Measure subtitle
    sub_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
    sub_w = sub_bbox[2] - sub_bbox[0]
    sub_x = (width - sub_w) // 2
    sub_y = title_y + title_h + 30

    # Draw semi-transparent dark backdrop behind title + subtitle
    pad_x, pad_y = 60, 40
    backdrop_left = min(title_x, sub_x) - pad_x
    backdrop_top = title_y - pad_y
    backdrop_right = max(title_x + title_w, sub_x + sub_w) + pad_x
    backdrop_bottom = sub_y + (sub_bbox[3] - sub_bbox[1]) + pad_y

    # Rounded rectangle backdrop
    backdrop = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    bd = ImageDraw.Draw(backdrop)
    bd.rounded_rectangle(
        [backdrop_left, backdrop_top, backdrop_right, backdrop_bottom],
        radius=24, fill=(0, 0, 0, 180),
    )
    img = Image.alpha_composite(img, backdrop)
    draw = ImageDraw.Draw(img)

    # Title text (white, with subtle shadow)
    for dx, dy in [(2, 2), (-1, -1), (2, 0), (0, 2)]:
        draw.multiline_text((title_x + dx, title_y + dy), title,
                            fill=(0, 0, 0, 100), font=title_font, align="center")
    draw.multiline_text((title_x, title_y), title,
                        fill=(255, 255, 255, 255), font=title_font, align="center")

    # Subtitle
    draw.text((sub_x, sub_y), subtitle,
              fill=(255, 255, 255, 210), font=subtitle_font)

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


def create_keyword_overlay(keyword, output_path, width=1920, height=1080):
    """Create transparent PNG with a single keyword and semi-transparent rounded backdrop."""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    try:
        kw_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 60)
    except (OSError, IOError):
        kw_font = ImageFont.load_default()

    # Measure keyword text
    bbox = draw.textbbox((0, 0), keyword, font=kw_font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    text_x = (width - text_w) // 2
    text_y = (height - text_h) // 2

    # Semi-transparent rounded rectangle backdrop
    pad_x, pad_y = 50, 30
    backdrop = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    bd = ImageDraw.Draw(backdrop)
    bd.rounded_rectangle(
        [text_x - pad_x, text_y - pad_y, text_x + text_w + pad_x, text_y + text_h + pad_y],
        radius=20, fill=(0, 0, 0, 160),
    )
    img = Image.alpha_composite(img, backdrop)
    draw = ImageDraw.Draw(img)

    # Text shadow
    for dx, dy in [(2, 2), (0, 2), (2, 0)]:
        draw.text((text_x + dx, text_y + dy), keyword,
                  fill=(0, 0, 0, 100), font=kw_font)
    # White text
    draw.text((text_x, text_y), keyword,
              fill=(255, 255, 255, 255), font=kw_font)

    img.save(output_path, "PNG")


def build_clip_reel(clips_dir, target_duration, output_path):
    """Build a clip reel: xfade 5 clips into one segment, then loop to fill duration."""
    clip_files = sorted(glob.glob(os.path.join(clips_dir, "clip*.mp4")))
    if not clip_files:
        return False

    durations = [get_duration(f) for f in clip_files]

    # Step 1: xfade the 5 clips into one seamless segment
    n = len(clip_files)
    inputs = []
    for f in clip_files:
        inputs.extend(["-i", f])

    filters = []
    for i in range(n):
        filters.append(
            f"[{i}:v]scale=1920:1080:force_original_aspect_ratio=increase,"
            f"crop=1920:1080,setsar=1,setpts=PTS-STARTPTS,fps=30[s{i}]"
        )

    cumulative = durations[0]
    prev = "s0"
    for i in range(1, n):
        offset = max(cumulative - XFADE_DUR, 0.5)
        out_label = f"x{i}" if i < n - 1 else "seg"
        filters.append(
            f"[{prev}][s{i}]xfade=transition=fade:duration={XFADE_DUR}:offset={offset:.3f}[{out_label}]"
        )
        cumulative = offset + durations[i]
        prev = out_label

    filter_str = ";\n".join(filters)

    # Write segment to a temp file, then loop it
    with tempfile.TemporaryDirectory() as td:
        seg_path = os.path.join(td, "segment.mp4")

        cmd = ["ffmpeg", "-y"] + inputs + [
            "-filter_complex", filter_str,
            "-map", "[seg]",
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-pix_fmt", "yuv420p", "-an",
            seg_path,
        ]

        print(f"  Building segment ({n} clips with dissolves)...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  Segment ERROR: {result.stderr[-600:]}")
            return False

        seg_dur = get_duration(seg_path)
        loops_needed = int(target_duration / seg_dur) + 1
        print(f"  Segment: {seg_dur:.1f}s, looping {loops_needed}x for {target_duration:.0f}s target")

        # Step 2: Loop the segment to fill target duration
        cmd2 = [
            "ffmpeg", "-y",
            "-stream_loop", str(loops_needed),
            "-i", seg_path,
            "-t", str(target_duration),
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-pix_fmt", "yuv420p", "-an",
            output_path,
        ]

        print(f"  Looping to full duration...")
        result2 = subprocess.run(cmd2, capture_output=True, text=True)
        if result2.returncode != 0:
            print(f"  Loop ERROR: {result2.stderr[-600:]}")
            return False

    return True


def compute_keyword_timings(keywords, duration, start_offset=15, fade_in=1, hold=3, fade_out=1):
    """Compute start/end times for keyword overlays, evenly spaced after start_offset.
    Each keyword: fade_in + hold + fade_out = total visible time (5s default).
    Returns list of (keyword, start_time, end_time) tuples."""
    total_per_kw = fade_in + hold + fade_out
    available = duration - start_offset - 10  # leave 10s buffer at end
    if available < total_per_kw:
        return []
    n = len(keywords)
    spacing = available / n
    timings = []
    for i, kw in enumerate(keywords):
        start = start_offset + i * spacing
        end = start + total_per_kw
        timings.append((kw, round(start, 2), round(end, 2)))
    return timings


def build_video(video_def):
    audio_path = os.path.join(BASE, video_def["audio"])
    clips_dir = os.path.join(BASE, video_def["clips_dir"])
    output_path = os.path.join(BASE, video_def["output"])
    title = video_def["title"]
    subtitle = video_def["subtitle"]
    keywords = video_def.get("keywords", [])
    thumb_path = output_path.replace(".mp4", "-thumb.jpg")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    if not os.path.exists(audio_path):
        print(f"  SKIP: Audio not found: {audio_path}")
        return

    duration = get_duration(audio_path)
    print(f"  Audio duration: {duration:.1f}s")

    with tempfile.TemporaryDirectory() as tmpdir:
        overlay_path = os.path.join(tmpdir, "overlay.png")
        reel_path = os.path.join(tmpdir, "reel.mp4")

        # Step 1: Create clip reel with crossfade dissolves
        if not build_clip_reel(clips_dir, duration, reel_path):
            print(f"  SKIP: Could not build clip reel from {clips_dir}")
            return

        # Step 2: Create title overlay
        print(f"  Creating title overlay...")
        create_title_overlay(title, subtitle, overlay_path)

        # Step 3: Create keyword overlay PNGs and compute timings
        kw_timings = compute_keyword_timings(keywords, duration)
        kw_paths = []
        for i, (kw, start, end) in enumerate(kw_timings):
            kw_path = os.path.join(tmpdir, f"kw_{i:02d}.png")
            create_keyword_overlay(kw, kw_path)
            kw_paths.append(kw_path)
            print(f"  Keyword '{kw}' @ {start:.0f}s-{end:.0f}s")

        # Step 4: Composite reel + title overlay + keyword overlays + audio
        # Build inputs list
        inputs = [
            "-i", reel_path,                        # 0: clip reel
            "-loop", "1", "-i", overlay_path,        # 1: title overlay
        ]
        for kw_path in kw_paths:
            inputs.extend(["-loop", "1", "-i", kw_path])
        inputs.extend(["-i", audio_path])            # last input: audio
        audio_idx = 2 + len(kw_paths)

        # Build filter_complex
        filter_lines = []
        # Darken background
        filter_lines.append(f"[0:v]eq=brightness=-0.12:saturation=0.85[bg]")
        # Title overlay — fade in at 1s, fade out starting at 10s
        filter_lines.append(
            f"[1:v]format=rgba,"
            f"fade=t=in:st=1:d=2:alpha=1,"
            f"fade=t=out:st=10:d=3:alpha=1[title]"
        )
        # Composite title onto background
        filter_lines.append(
            f"[bg][title]overlay=0:0:shortest=1[comp0]"
        )

        # Chain keyword overlays
        prev_label = "comp0"
        for i, (kw, start, end) in enumerate(kw_timings):
            fade_in_end = start + 1
            fade_out_start = end - 1
            kw_input = i + 2  # inputs 2, 3, 4, ...
            kw_label = f"kw{i}"
            out_label = f"comp{i + 1}"
            # Fade in over 1s, fade out over 1s
            filter_lines.append(
                f"[{kw_input}:v]format=rgba,"
                f"fade=t=in:st={start}:d=1:alpha=1,"
                f"fade=t=out:st={fade_out_start}:d=1:alpha=1[{kw_label}]"
            )
            filter_lines.append(
                f"[{prev_label}][{kw_label}]overlay=0:0:"
                f"enable='between(t,{start},{end})':shortest=1[{out_label}]"
            )
            prev_label = out_label

        # Video fade in/out
        filter_lines.append(
            f"[{prev_label}]fade=t=in:st=0:d=2,"
            f"fade=t=out:st={duration - 3}:d=3[vout]"
        )
        # Audio fade out
        filter_lines.append(
            f"[{audio_idx}:a]afade=t=out:st={duration - 3}:d=3[aout]"
        )

        filter_complex = ";\n".join(filter_lines)

        cmd = [
            "ffmpeg", "-y",
        ] + inputs + [
            "-filter_complex", filter_complex,
            "-map", "[vout]", "-map", "[aout]",
            "-c:v", "libx264", "-preset", "medium", "-crf", "26",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart",
            "-t", str(duration),
            output_path,
        ]

        print(f"  Compositing final video ({1 + len(kw_timings)} overlays)...")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"  ERROR: {result.stderr[-800:]}")
            return

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"  Saved: {output_path} ({size_mb:.1f} MB)")

    # Generate thumbnail
    subprocess.run([
        "ffmpeg", "-y", "-i", output_path,
        "-ss", "4", "-vframes", "1", "-vf", "scale=1280:720",
        thumb_path,
    ], capture_output=True, text=True)

    if os.path.exists(thumb_path):
        print(f"  Thumbnail: {thumb_path}")


if __name__ == "__main__":
    import sys

    print("=== Salus Video Generator ===\n")

    only = None
    if "--only" in sys.argv:
        idx = sys.argv.index("--only")
        if idx + 1 < len(sys.argv):
            only = int(sys.argv[idx + 1])

    for i, vdef in enumerate(videos, 1):
        if only is not None and i != only:
            continue
        print(f"[{i}/4] {vdef['title'].replace(chr(10), ' ')}")
        build_video(vdef)
        print()

    print("Done!")
