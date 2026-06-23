"""Draft SEO blog content for Laura to review and publish.

Examples:
  python -m content.draft_post --type venue --venue "Crathorne Hall"
  python -m content.draft_post --type city --city "Durham"
  python -m content.draft_post --type wedding --couple "Anna & Tom" --venue "Newton Hall"

Output is a markdown draft + a suggested SEO title and meta description. ALWAYS
review and edit before publishing — this is a first draft in Laura's voice, not
a finished post.
"""
from __future__ import annotations

import argparse

from utils.config import load_config, output_dir
from utils.llm import complete

SYSTEM = (
    "You write warm, genuine blog content for Laura Beasley, a North East "
    "England wedding photographer with a relaxed documentary style. Write in "
    "first person as Laura. Natural, not salesy. Weave location keywords in "
    "naturally. Avoid clichés and AI-sounding filler."
)


def prompt_for(args, cfg) -> str:
    region = cfg["service_area"]["primary_region"]
    if args.type == "venue":
        return (f"Write a 600-word wedding venue guide blog post for couples "
                f"considering '{args.venue}' in {region}. Cover the venue's "
                f"character, photo opportunities, and why it suits a relaxed "
                f"documentary style. Target keyword: '{args.venue} wedding "
                f"photographer'. End with a soft call to enquire.")
    if args.type == "city":
        return (f"Write a 600-word local page for 'Wedding photographer in "
                f"{args.city}'. Mention notable {args.city} venues and what it's "
                f"like to get married there, in Laura's documentary style. "
                f"Target keyword: 'wedding photographer {args.city}'.")
    if args.type == "wedding":
        return (f"Write a 500-word real-wedding feature for {args.couple}'s "
                f"wedding at {args.venue}. Warm storytelling about the day. "
                f"Target keyword: '{args.venue} wedding photographer'.")
    raise SystemExit("--type must be venue, city or wedding")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--type", required=True, choices=["venue", "city", "wedding"])
    p.add_argument("--venue", default="")
    p.add_argument("--city", default="")
    p.add_argument("--couple", default="")
    args = p.parse_args()
    cfg = load_config()

    body = complete(prompt_for(args, cfg), system=SYSTEM, quality=True, max_tokens=2000)
    meta = complete(
        f"For this blog post, give an SEO title (<=60 chars) and a meta "
        f"description (120-155 chars). Format exactly as:\nTITLE: ...\nMETA: ..."
        f"\n\nPost:\n{body[:1500]}",
        max_tokens=200,
    )

    slug = (args.venue or args.city or args.couple or "draft").lower().replace(" ", "-")
    out = f"<!-- REVIEW BEFORE PUBLISHING -->\n\n{meta}\n\n---\n\n{body}\n"
    path = output_dir() / f"draft-{args.type}-{slug}.md"
    path.write_text(out, encoding="utf-8")
    print(out)
    print(f"\n--- draft saved to {path} ---")


if __name__ == "__main__":
    main()
