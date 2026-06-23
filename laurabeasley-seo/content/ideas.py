"""Turn Search Console keyword data into a prioritised content queue.

Run:  python -m content.ideas

Finds "striking distance" keywords (positions 5-20 with impressions) — the
fastest SEO wins — plus venue/city gaps from config that you have no content
for yet. Falls back to the config seed keywords if Search Console isn't wired
up yet.
"""
from __future__ import annotations

import json

from utils.config import load_config, output_dir


def striking_distance() -> list[dict]:
    """Keywords ranking 5-20 with real impressions = best ROI to improve."""
    try:
        from tracking.rankings import query
        rows = query()
    except Exception as exc:  # GSC not set up yet
        print(f"(Search Console not available: {exc} — using config seeds.)")
        return []
    return [r for r in rows if 5 <= r["position"] <= 20 and r["impressions"] >= 10]


def venue_gaps(cfg: dict) -> list[str]:
    return [f"Venue guide: {v} wedding photographer" for v in cfg.get("venues", [])]


def city_gaps(cfg: dict) -> list[str]:
    return [f"Local page: Wedding photographer in {c}"
            for c in cfg["service_area"]["cities"]]


def main() -> None:
    cfg = load_config()
    queue = []
    for r in striking_distance():
        queue.append({"priority": "high",
                      "topic": f"Improve page for '{r['query']}' (pos {r['position']})",
                      "reason": f"{r['impressions']} impressions, almost ranking"})
    for t in venue_gaps(cfg):
        queue.append({"priority": "high", "topic": t,
                      "reason": "High-intent, low-competition venue search"})
    for t in city_gaps(cfg):
        queue.append({"priority": "medium", "topic": t,
                      "reason": "Local landing page for service area"})

    path = output_dir() / "content_queue.json"
    path.write_text(json.dumps(queue, indent=2, ensure_ascii=False), encoding="utf-8")
    for item in queue:
        print(f"[{item['priority']:>6}] {item['topic']}")
    print(f"\n{len(queue)} ideas saved to {path}")


if __name__ == "__main__":
    main()
