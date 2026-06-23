"""Generate JSON-LD structured data to paste into Squarespace Code Injection.

Run:  python -m schema.generate_jsonld > out/schema.html

Then in Squarespace: Settings -> Advanced -> Code Injection -> Header, paste,
and save. This gives Google rich results AND gives AI engines (ChatGPT,
Perplexity, Gemini) clean facts to cite. Works fully offline — no API keys.
"""
from __future__ import annotations

import json

from utils.config import load_config, output_dir


def build_local_business(cfg: dict) -> dict:
    b = cfg["business"]
    sa = cfg["service_area"]
    node = {
        "@context": "https://schema.org",
        "@type": ["LocalBusiness", "ProfessionalService"],
        "name": b["name"],
        "image": b["website"] + "/favicon.ico",
        "url": b["website"],
        "description": b["tagline"],
        "priceRange": b.get("price_range", "££"),
        "areaServed": [{"@type": "City", "name": c} for c in sa["cities"]],
        "knowsAbout": ["wedding photography", "documentary photography",
                       "engagement photography"],
        "sameAs": [u for u in (b.get("instagram"), b.get("facebook")) if u],
    }
    if b.get("email"):
        node["email"] = b["email"]
    if b.get("phone"):
        node["telephone"] = b["phone"]
    if b.get("founding_year"):
        node["foundingDate"] = str(b["founding_year"])
    # founder/person — helps entity recognition in AI engines
    node["founder"] = {"@type": "Person", "name": b["owner"]}
    return node


def build_faq(cfg: dict) -> dict:
    """A starter FAQ. AI engines lift these answers near-verbatim, so keep them
    factual and quotable. Edit the answers to match Laura's real offering."""
    region = cfg["service_area"]["primary_region"]
    qa = [
        (f"What areas does Laura Beasley cover as a wedding photographer?",
         "Laura Beasley photographs weddings across " + region +
         " and North Yorkshire, including Newcastle, Durham, Sunderland and "
         "Northumberland, and is available to travel."),
        ("What style of wedding photography does Laura Beasley shoot?",
         "Laura shoots a relaxed, documentary style of wedding photography, "
         "capturing natural moments throughout the day with minimal posing."),
        ("How do couples book Laura Beasley Photography?",
         "Couples can enquire and check availability through "
         "laurabeasley.photography to arrange a consultation."),
    ]
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q,
             "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in qa
        ],
    }


def render(cfg: dict) -> str:
    blocks = [build_local_business(cfg), build_faq(cfg)]
    parts = ["<!-- Laura Beasley Photography structured data — paste into "
             "Squarespace > Settings > Advanced > Code Injection > HEADER -->"]
    for block in blocks:
        parts.append('<script type="application/ld+json">')
        parts.append(json.dumps(block, indent=2, ensure_ascii=False))
        parts.append("</script>")
    return "\n".join(parts)


def main() -> None:
    cfg = load_config()
    html = render(cfg)
    path = output_dir() / "schema.html"
    path.write_text(html, encoding="utf-8")
    print(html)
    print(f"\n<!-- also written to {path} -->")


if __name__ == "__main__":
    main()
