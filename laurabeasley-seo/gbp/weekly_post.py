"""Draft a weekly Google Business Profile post.

Run:  python -m gbp.weekly_post --topic "Autumn wedding at Healey Barn"

Google treats each GBP post as a freshness signal that lifts local ranking, and
profiles posting weekly outrank static ones. This drafts the copy; paste it into
your Google Business Profile (or wire up the GBP API later for auto-posting).
"""
from __future__ import annotations

import argparse

from utils.config import load_config, output_dir
from utils.llm import complete


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--topic", required=True, help="What this week's post is about")
    args = p.parse_args()
    cfg = load_config()
    region = cfg["service_area"]["primary_region"]

    text = complete(
        f"Write a short Google Business Profile post (max 1500 chars, ideally "
        f"~80 words) for {cfg['business']['name']}, a {region} wedding "
        f"photographer. Topic: {args.topic}. Friendly, include one local "
        f"keyword naturally, and end with a clear call to action to enquire.",
        max_tokens=400,
    )
    path = output_dir() / "gbp_post.txt"
    path.write_text(text, encoding="utf-8")
    print(text)
    print(f"\n--- saved to {path}; paste into Google Business Profile ---")


if __name__ == "__main__":
    main()
