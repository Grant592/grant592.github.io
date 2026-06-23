"""Pull keyword positions, clicks and impressions from Google Search Console.

Run:  python -m tracking.rankings

SETUP (one-time, free):
  1. Google Cloud Console -> create project -> enable "Search Console API".
  2. Create an OAuth client (Desktop), download as client_secret.json into repo root.
  3. Add laurabeasley.photography as a property in Search Console.
  4. Run this module; a browser opens to authorise; token.json is cached.

Uses GSC's own position data as a free rank tracker (no paid SERP tool needed).
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from utils.config import env, load_config, output_dir

SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
ROOT = Path(__file__).resolve().parent.parent


def _service():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    token = ROOT / "token.json"
    creds = None
    if token.exists():
        creds = Credentials.from_authorized_user_file(str(token), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            secret = ROOT / "client_secret.json"
            if not secret.exists():
                raise SystemExit("Missing client_secret.json — see module docstring.")
            creds = InstalledAppFlow.from_client_secrets_file(
                str(secret), SCOPES).run_local_server(port=0)
        token.write_text(creds.to_json())
    return build("searchconsole", "v1", credentials=creds)


def query(days: int = 28) -> list[dict]:
    site = env("GSC_SITE_URL") or load_config()["business"]["website"]
    end = dt.date.today()
    start = end - dt.timedelta(days=days)
    body = {
        "startDate": start.isoformat(),
        "endDate": end.isoformat(),
        "dimensions": ["query"],
        "rowLimit": 250,
    }
    resp = _service().searchanalytics().query(siteUrl=site, body=body).execute()
    rows = []
    for r in resp.get("rows", []):
        rows.append({
            "query": r["keys"][0],
            "clicks": r["clicks"],
            "impressions": r["impressions"],
            "ctr": round(r["ctr"], 4),
            "position": round(r["position"], 1),
        })
    return rows


def main() -> None:
    rows = query()
    rows.sort(key=lambda r: r["impressions"], reverse=True)
    path = output_dir() / "rankings.json"
    path.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{'pos':>5}  {'clk':>5}  {'impr':>6}  query")
    for r in rows[:25]:
        print(f"{r['position']:>5}  {r['clicks']:>5}  {r['impressions']:>6}  {r['query']}")
    print(f"\nSaved {len(rows)} rows to {path}")


if __name__ == "__main__":
    main()
