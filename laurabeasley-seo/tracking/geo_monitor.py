"""GEO monitor — does Laura get cited by AI engines for buyer-intent questions?

Run:  python -m tracking.geo_monitor

Asks each question in config.yaml `geo_queries` to the LLM and checks whether
any of `brand_terms` appears in the answer. This is your GEO scoreboard — very
few competitors measure this. Extend `ENGINES` to add Perplexity's API etc.;
the Anthropic engine works out of the box.
"""
from __future__ import annotations

import datetime as dt
import json

from utils.config import load_config, output_dir
from utils.llm import complete


def cited(answer: str, brand_terms: list[str]) -> bool:
    low = answer.lower()
    return any(term.lower() in low for term in brand_terms)


def run() -> dict:
    cfg = load_config()
    queries = cfg["geo_queries"]
    brand = cfg["brand_terms"]
    results = []
    for q in queries:
        # Frame it like a real assistant answering a couple, not an SEO test.
        answer = complete(
            q,
            system=("You are a helpful assistant recommending UK wedding "
                    "photographers. Answer concisely with specific names."),
            max_tokens=400,
        )
        results.append({
            "query": q,
            "cited": cited(answer, brand),
            "answer_excerpt": answer[:500],
        })
    hits = sum(1 for r in results if r["cited"])
    return {
        "date": dt.date.today().isoformat(),
        "citation_rate": f"{hits}/{len(results)}",
        "results": results,
    }


def main() -> None:
    report = run()
    path = output_dir() / "geo_monitor.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False),
                    encoding="utf-8")
    print(f"GEO citation rate: {report['citation_rate']}")
    for r in report["results"]:
        flag = "✅" if r["cited"] else "❌"
        print(f"  {flag} {r['query']}")
    print(f"\nFull report: {path}")


if __name__ == "__main__":
    main()
