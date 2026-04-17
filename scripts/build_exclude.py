#!/usr/bin/env python3
"""
Build exclude list of PMIDs from past N days of reports.
Reads docs/reported_pmids.json and collects all PMIDs within the lookback window.
"""

import json
import sys
import argparse
from datetime import datetime, timezone, timedelta


def main():
    parser = argparse.ArgumentParser(description="Build PMID exclude list")
    parser.add_argument("--days", type=int, default=7, help="How many past days to look back")
    parser.add_argument("--tracking", default="docs/reported_pmids.json", help="Tracking file path")
    parser.add_argument("--output", default="reported_pmids.json", help="Output exclude file")
    args = parser.parse_args()

    tz_taipei = timezone(timedelta(hours=8))
    today = datetime.now(tz_taipei).date()
    cutoff = today - timedelta(days=args.days)

    exclude_pmids = set()

    try:
        with open(args.tracking, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"[INFO] No tracking file found at {args.tracking}, starting fresh", file=sys.stderr)
        data = {}
    except Exception as e:
        print(f"[WARN] Could not read tracking file: {e}", file=sys.stderr)
        data = {}

    for date_str, pmid_list in data.items():
        if not isinstance(pmid_list, list):
            continue
        try:
            report_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            if report_date >= cutoff:
                exclude_pmids.update(str(p) for p in pmid_list)
        except ValueError:
            continue

    print(f"[INFO] Excluding {len(exclude_pmids)} PMIDs from past {args.days} days", file=sys.stderr)

    result = sorted(exclude_pmids)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"[INFO] Exclude list saved to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
