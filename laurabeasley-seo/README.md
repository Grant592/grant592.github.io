# Laura Beasley Photography — SEO / GEO Automation Toolkit

A semi-automated toolkit to grow wedding-photography bookings for
**laurabeasley.photography** through better SEO, local search (Google Business
Profile), and GEO (getting cited by ChatGPT / Perplexity / Gemini / Google AI
Overviews).

The website stays on **Squarespace**. This toolkit runs *alongside* it: it
audits the site, drafts content and schema for you to review, and monitors how
you're performing in both classic search and AI answers. Everything that
changes the live site is produced as **paste-ready blocks** so you keep full
control.

> Market: North East England + North Yorkshire — Newcastle, Durham, Sunderland,
> Northumberland, North Yorkshire.

---

## What's in the box

| Module | What it does | Status |
|--------|--------------|--------|
| `schema/generate_jsonld.py` | Generates LocalBusiness + FAQ + Review JSON-LD to paste into Squarespace Code Injection | ✅ Works offline |
| `audits/site_audit.py` | Crawls the live site + runs Google PageSpeed; flags missing titles, meta, alt text, schema | ✅ Works (PageSpeed key optional) |
| `tracking/geo_monitor.py` | Asks AI engines your target questions and reports whether you're cited | ✅ Needs LLM API key |
| `tracking/rankings.py` | Pulls keyword positions & clicks from Google Search Console | 🔑 Needs GSC credentials |
| `content/ideas.py` | Turns Search Console keyword gaps into a prioritised topic queue | 🔑 Needs GSC credentials |
| `content/draft_post.py` | Drafts a real-wedding feature / venue guide / city page for you to review | ✅ Needs LLM API key |
| `images/alt_text.py` | Writes SEO alt text for portfolio images using a vision model | ✅ Needs LLM API key |
| `gbp/weekly_post.py` | Drafts a weekly Google Business Profile post | ✅ Needs LLM API key |
| `report/weekly_digest.py` | Rolls everything into one weekly email/markdown digest | ✅ |

All scheduling is free via **GitHub Actions** (`.github/workflows/weekly.yml`).

---

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # add your API keys
# edit config.yaml with your venues / cities / keywords
```

### Immediate wins (no API keys needed)

```bash
# 1. Generate schema to paste into Squarespace today
python -m schema.generate_jsonld > out/schema.html

# 2. Audit the live site for SEO gaps
python -m audits.site_audit
```

Then in Squarespace: **Settings → Advanced → Code Injection → Header**, paste
the contents of `out/schema.html`, save. That alone gives you LocalBusiness
structured data that both Google and AI engines read.

### Once you've added keys

```bash
python -m tracking.geo_monitor      # are you cited by ChatGPT/Perplexity?
python -m content.draft_post --type venue --venue "Crathorne Hall"
python -m report.weekly_digest
```

---

## Configuration

Everything business-specific lives in `config.yaml` — cities, venues, target
keywords, brand details, and the questions used to test AI engines. Edit that
file; no code changes needed.

## API keys (all free or near-free)

| Service | Used by | Cost | Where |
|---------|---------|------|-------|
| Anthropic API | content, GEO, alt text | ~£5–15/mo at this volume | console.anthropic.com |
| Google PageSpeed Insights | audit | Free | Google Cloud Console |
| Google Search Console API | rankings, ideas | Free | Google Cloud Console |
| Google Business Profile API | GBP posts | Free | Google Cloud Console |

See `.env.example` for variable names. None are committed — `.env` is gitignored.

---

## Roadmap

- **Phase 1 (this scaffold):** audit, schema, GEO monitor, content drafting.
- **Phase 2:** wire up Search Console + GBP credentials for live data.
- **Phase 3:** weekly automated digest via GitHub Actions.
- **Phase 4:** review-request flow + directory/citation tracking.
