"""Roll everything into one weekly digest (markdown, optionally emailed).

Run:  python -m report.weekly_digest

Runs the audit + GEO monitor (and rankings if GSC is configured), then writes a
single digest with this week's numbers and a short to-do list. Designed to be
triggered weekly by GitHub Actions.
"""
from __future__ import annotations

import datetime as dt

from utils.config import load_config, output_dir


def _safe(fn, label):
    try:
        return fn()
    except Exception as exc:  # noqa: BLE001
        return f"_{label} unavailable: {exc}_"


def build() -> str:
    cfg = load_config()
    today = dt.date.today().isoformat()
    lines = [f"# Weekly SEO/GEO digest — {cfg['business']['name']}",
             f"_{today}_\n"]

    # --- GEO citation rate ---
    def geo():
        from tracking.geo_monitor import run
        r = run()
        rows = "\n".join(
            f"- {'✅' if x['cited'] else '❌'} {x['query']}" for x in r["results"])
        return f"**AI citation rate: {r['citation_rate']}**\n{rows}"
    lines.append("## GEO — are AI engines recommending you?")
    lines.append(_safe(geo, "GEO monitor"))
    lines.append("")

    # --- Rankings (if GSC wired up) ---
    def ranks():
        from tracking.rankings import query
        rows = sorted(query(), key=lambda r: r["impressions"], reverse=True)[:10]
        body = "\n".join(
            f"- pos {r['position']} · {r['clicks']} clicks · {r['query']}"
            for r in rows)
        return body or "_No data yet._"
    lines.append("## Top search queries (last 28 days)")
    lines.append(_safe(ranks, "Search Console"))
    lines.append("")

    # --- Site audit ---
    def audit():
        from audits.site_audit import audit_page
        return "\n".join(f"- {x}" for x in audit_page(cfg["business"]["website"]))
    lines.append("## Homepage audit")
    lines.append(_safe(audit, "Audit"))
    lines.append("")

    lines.append("## Suggested actions this week")
    lines.append("- [ ] Publish one venue or real-wedding post (content.draft_post)")
    lines.append("- [ ] Post once to Google Business Profile (gbp.weekly_post)")
    lines.append("- [ ] Request a Google review from your most recent couple")
    return "\n".join(lines)


def main() -> None:
    digest = build()
    path = output_dir() / "weekly_digest.md"
    path.write_text(digest, encoding="utf-8")
    print(digest)
    print(f"\n--- saved to {path} ---")


if __name__ == "__main__":
    main()
