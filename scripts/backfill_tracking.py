#!/usr/bin/env python3
"""One-time script to backfill reported_pmids.json from existing HTML reports."""

import re
import glob
import json
import os

docs_dir = "docs"
pattern = re.compile(r'pubmed\.ncbi\.nlm\.nih\.gov/(\d+)')
tracking = {}

for html_file in sorted(glob.glob(os.path.join(docs_dir, "autism-*.html"))):
    basename = os.path.basename(html_file)
    date_match = re.search(r'autism-(\d{4}-\d{2}-\d{2})\.html', basename)
    if not date_match:
        continue
    date_str = date_match.group(1)
    
    with open(html_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    pmids = list(set(pattern.findall(content)))
    if pmids:
        tracking[date_str] = sorted(pmids)
        print(f"{date_str}: {len(pmids)} PMIDs")

output_path = os.path.join(docs_dir, "reported_pmids.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(tracking, f, ensure_ascii=False, indent=2)
print(f"\nSaved to {output_path}")
print(f"Total dates: {len(tracking)}, Total PMIDs: {sum(len(v) for v in tracking.values())}")
