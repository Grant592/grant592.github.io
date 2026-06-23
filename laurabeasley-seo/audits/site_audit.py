"""Crawl the live site and flag on-page SEO gaps; optionally run PageSpeed.

Run:  python -m audits.site_audit

Checks the homepage (and any URLs passed) for: title tag, meta description,
H1, image alt-text coverage, and presence of JSON-LD schema. With a
PAGESPEED_API_KEY set it also reports Core Web Vitals. No key required for the
on-page checks.
"""
from __future__ import annotations

import sys

import requests
from bs4 import BeautifulSoup

from utils.config import env, load_config, output_dir

UA = {"User-Agent": "Mozilla/5.0 (compatible; LBP-SEO-Audit/1.0)"}


def fetch(url: str) -> BeautifulSoup | None:
    try:
        r = requests.get(url, headers=UA, timeout=20)
        r.raise_for_status()
        return BeautifulSoup(r.text, "html.parser")
    except requests.RequestException as exc:
        print(f"  ! could not fetch {url}: {exc}")
        return None


def audit_page(url: str) -> list[str]:
    findings: list[str] = []
    soup = fetch(url)
    if soup is None:
        return [f"FAIL: could not load {url}"]

    title = (soup.title.string or "").strip() if soup.title else ""
    if not title:
        findings.append("Missing <title> tag.")
    elif len(title) < 30:
        findings.append(f"Thin title ({len(title)} chars): '{title}' — "
                        "include style + location keywords.")

    desc = soup.find("meta", attrs={"name": "description"})
    if not desc or not desc.get("content", "").strip():
        findings.append("Missing meta description.")
    elif not (120 <= len(desc["content"]) <= 160):
        findings.append(f"Meta description length {len(desc['content'])} "
                        "(aim 120–160 chars).")

    h1s = soup.find_all("h1")
    if not h1s:
        findings.append("No <h1> on page.")
    elif len(h1s) > 1:
        findings.append(f"{len(h1s)} <h1> tags — use exactly one.")

    imgs = soup.find_all("img")
    if imgs:
        missing = [i for i in imgs if not i.get("alt", "").strip()]
        pct = 100 * len(missing) // len(imgs)
        if missing:
            findings.append(f"{len(missing)}/{len(imgs)} images ({pct}%) "
                            "missing alt text — run images.alt_text.")
    else:
        findings.append("No <img> tags found (JS-rendered? check manually).")

    if not soup.find_all("script", attrs={"type": "application/ld+json"}):
        findings.append("No JSON-LD schema — run schema.generate_jsonld and "
                        "paste into Code Injection.")

    return findings or ["OK — no major on-page issues detected."]


def pagespeed(url: str) -> str | None:
    key = env("PAGESPEED_API_KEY")
    if not key:
        return None
    api = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
    try:
        r = requests.get(api, params={"url": url, "key": key,
                                      "strategy": "mobile"}, timeout=60)
        r.raise_for_status()
        score = r.json()["lighthouseResult"]["categories"]["performance"]["score"]
        return f"Mobile performance score: {int(score * 100)}/100"
    except (requests.RequestException, KeyError) as exc:
        return f"PageSpeed lookup failed: {exc}"


def main() -> None:
    cfg = load_config()
    base = cfg["business"]["website"]
    urls = sys.argv[1:] or [base]
    lines = ["# Site audit\n"]
    for url in urls:
        lines.append(f"## {url}")
        for f in audit_page(url):
            lines.append(f"- {f}")
        ps = pagespeed(url)
        if ps:
            lines.append(f"- {ps}")
        lines.append("")
    report = "\n".join(lines)
    (output_dir() / "audit.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
