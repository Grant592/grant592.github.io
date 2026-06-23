"""Generate SEO alt text for portfolio images using a vision model.

Run:  python -m images.alt_text path/to/folder
      python -m images.alt_text image1.jpg image2.jpg

Alt text is one of the strongest ranking signals for photographer websites
(Google reads it as the primary description of the image). Outputs a CSV mapping
filename -> alt text that you paste into each image's alt field in Squarespace.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

from utils.config import load_config, output_dir
from utils.llm import ask_with_image

EXTS = {".jpg", ".jpeg", ".png", ".webp"}
MEDIA = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
         ".webp": "image/webp"}


def gather(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for p in paths:
        path = Path(p)
        if path.is_dir():
            files += [f for f in path.rglob("*") if f.suffix.lower() in EXTS]
        elif path.suffix.lower() in EXTS:
            files.append(path)
    return files


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python -m images.alt_text <folder|images...>")
    cfg = load_config()
    region = cfg["service_area"]["primary_region"]
    files = gather(sys.argv[1:])
    if not files:
        raise SystemExit("No images found.")

    rows = []
    instruction = (
        "Write concise, natural alt text (max ~125 chars) for this wedding "
        f"photo by a {region} wedding photographer. Describe what's visible "
        "(people, setting, moment). Include a location/venue only if obviously "
        "implied. No 'image of'. Output only the alt text.")
    for f in files:
        try:
            alt = ask_with_image(instruction, f.read_bytes(),
                                 MEDIA.get(f.suffix.lower(), "image/jpeg"))
        except Exception as exc:  # noqa: BLE001
            alt = f"(error: {exc})"
        rows.append((f.name, alt))
        print(f"{f.name}\n  -> {alt}\n")

    path = output_dir() / "alt_text.csv"
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["filename", "alt_text"])
        w.writerows(rows)
    print(f"Saved {len(rows)} alt texts to {path}")


if __name__ == "__main__":
    main()
