#!/usr/bin/env python3
"""
Update the reported_pmids.json tracking file after generating a daily report.
Adds today's PMIDs and prunes entries older than keep_days.
"""

import json
import sys
import argparse
from datetime import datetime, timezone, timedelta


def main():
    parser = argparse.ArgumentParser(description="Update reported PMIDs tracking")
    parser.add_argument("--papers", required=True, help="Papers JSON from fetch_papers.py")
    parser.add_argument("--tracking", default="docs/reported_pmids.json", help="Tracking file")
    parser.add_argument("--date", required=True, help="Report date (YYYY-MM-DD)")
    parser.add_argument("--keep-days", type=int, default=7, help="Days of history to keep")
    args = parser.parse_args()

    tz_taipei = timezone(timedelta(hours=8))
    today = datetime.now(tz_taipei).date()
    cutoff = today - timedelta(days=args.keep_days)

    try:
        with open(args.tracking, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}
    except Exception as e:
        print(f"[WARN] Could not read tracking file, starting fresh: {e}", file=sys.stderr)
        data = {}

    if not isinstance(data, dict):
        data = {}

    today_pmids = []
    try:
        with open(args.papers, "r", encoding="utf-8") as f:
            papers_data = json.load(f)
        for p in papers_data.get("papers", []):
            pmid = str(p.get("pmid", ""))
            if pmid:
                today_pmids.append(pmid)
    except Exception as e:
        print(f"[WARN] Could not read papers file: {e}", file=sys.stderr)

    if today_pmids:
        data[args.date] = today_pmids
        print(f"[INFO] Added {len(today_pmids)} PMIDs for {args.date}", file=sys.stderr)

    pruned_keys = [
        k for k in data
        if isinstance(k, str) and len(k) == 10
        and k[4] == "-" and k[7] == "-"
    ]
    for k in pruned_keys:
        try:
            d = datetime.strptime(k, "%Y-%m-%d").date()
            if d < cutoff:
                del data[k]
        except ValueError:
            pass

    with open(args.tracking, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[INFO] Tracking file updated: {args.tracking}", file=sys.stderr)


if __name__ == "__main__":
    main()
