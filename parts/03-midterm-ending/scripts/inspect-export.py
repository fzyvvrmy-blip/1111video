#!/usr/bin/env python3
"""Inspect the real v2 exports and save decoded review frames and a QA record."""

import array
import io
import json
from pathlib import Path
import subprocess
import wave

from PIL import Image, ImageChops, ImageDraw

PART = Path(__file__).resolve().parents[1]
OUT = PART / "renders/part03-animation-v2"
KEYS = PART / "keyframes/animation-v2"


def probe(path):
    return json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries",
        "stream=codec_type,codec_name,width,height,r_frame_rate,nb_frames,sample_rate,channels:format=duration",
        "-of", "json", str(path),
    ]))


def frame(path, timestamp):
    data = subprocess.check_output([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", str(timestamp),
        "-i", str(path), "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-",
    ])
    return Image.open(io.BytesIO(data)).convert("RGB")


def is_black(image):
    return all(low == high == 0 for low, high in image.getextrema())


def main():
    video = OUT / "part03-draft-1080x2376.mp4"
    preview = OUT / "part03-preview-540p.mp4"
    metadata = {}
    for path, dimensions in ((video, (1080, 2376)), (preview, (540, 1188))):
        info = probe(path)
        stream = next(s for s in info["streams"] if s["codec_type"] == "video")
        audio = next(s for s in info["streams"] if s["codec_type"] == "audio")
        assert (stream["width"], stream["height"]) == dimensions
        assert stream["r_frame_rate"] == "30/1" and stream["nb_frames"] == "900"
        assert float(info["format"]["duration"]) == 30
        assert (audio["sample_rate"], audio["channels"]) == ("48000", 2)
        subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-i", str(path), "-f", "null", "-"], check=True)
        assert is_black(frame(path, 0)) and is_black(frame(path, 29.966667))
        metadata[path.name] = info

    samples = [("start", 0), ("notifications", 5.2), ("transition", 6.45),
               ("orders", 7.4), ("receipt1", 9.75), ("receipt2", 11.25),
               ("receipt3", 12.65), ("four-signed", 14.1), ("insufficient", 15.3),
               ("same-order", 16.6), ("refund", 18.1), ("pf", 23.1),
               ("ending", 27.7), ("end", 29.966667)]
    frames = {}
    for name, timestamp in samples:
        image = frame(video, timestamp)
        frames[name] = image
        image.resize((540, 1188)).save(OUT / f"encoded-{name}.jpg", quality=94)

    peaks = {}
    for name in ("notifications.wav", "operations.wav", "preview-mix.wav"):
        with wave.open(str(OUT / name)) as audio:
            pcm = array.array("h", audio.readframes(audio.getnframes()))
            peaks[name] = max(abs(n) for n in pcm) / 32767
            assert audio.getnchannels() == 2 and peaks[name] < .92

    october = Image.open(PART / "assets/lockscreen-v2-oct22.png").convert("RGB")
    november = Image.open(PART / "assets/lockscreen-v2-nov02.png").convert("RGB")
    bbox = ImageChops.difference(october, november).getbbox()
    assert bbox and bbox[0] >= 260 and bbox[1] >= 544 and bbox[2] <= 820 and bbox[3] <= 862

    selected = ["notifications", "transition", "orders", "four-signed", "insufficient", "refund", "pf", "ending", "end"]
    sheet = Image.new("RGB", (1080, 2466), "#e8e1ef")
    draw = ImageDraw.Draw(sheet)
    for i, name in enumerate(selected):
        x, y = i % 3 * 360, i // 3 * 822
        sheet.paste(frames[name].resize((360, 792)), (x, y))
        draw.text((x + 10, y + 799), name, fill="#22162f")
    sheet.save(KEYS / "review-encoded-v2.jpg", quality=92)

    qa = {"exports": metadata, "completeDecode": True, "blackStartEnd": True,
          "audioPeaks": peaks, "lockscreenDateOnlyChangeBBox": bbox,
          "checkedEncodedFrames": dict(samples), "fontActual": "Noto Sans CJK SC",
          "ledger": json.loads((OUT / "receipt-ledger.json").read_text())}
    for path in (OUT / "qa.json", KEYS / "export-check.json"):
        path.write_text(json.dumps(qa, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(qa, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
