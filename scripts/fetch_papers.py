#!/usr/bin/env python3
"""
Fetch latest autism research papers from PubMed E-utilities API.
Targets core autism journals and covers major autism spectrum topics.
"""

import json
import sys
import argparse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from urllib.request import urlopen, Request
from urllib.error import URLError
from urllib.parse import quote_plus

PUBMED_SEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_FETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

CORE_JOURNALS = [
    "Molecular Autism",
    "Autism Research",
    "Journal of Autism and Developmental Disorders",
    "Autism",
    "Review Journal of Autism and Developmental Disorders",
    "Research in Autism Spectrum Disorders",
    "Focus on Autism and Other Developmental Disabilities",
]

ADJACENT_JOURNALS = [
    "Journal of Neurodevelopmental Disorders",
    "Developmental Cognitive Neuroscience",
    "Journal of Child Psychology and Psychiatry",
    "Biological Psychiatry",
    "Advances in Neurodevelopmental Disorders",
]

JOURNALS = CORE_JOURNALS + ADJACENT_JOURNALS

SEARCH_QUERIES = [
    '("autism spectrum disorder"[Title/Abstract] OR autism[Title/Abstract] OR ASD[Title/Abstract])',
    '("autism spectrum disorder"[Title/Abstract] OR autism[Title/Abstract] OR ASD[Title/Abstract]) AND ("social communication"[Title/Abstract] OR "sensory processing"[Title/Abstract] OR "restricted repetitive behaviors"[Title/Abstract])',
    '("autism spectrum disorder"[Title/Abstract] OR autism[Title/Abstract] OR ASD[Title/Abstract]) AND (anxiety[Title/Abstract] OR depression[Title/Abstract] OR ADHD[Title/Abstract] OR sleep[Title/Abstract])',
    '("autism spectrum disorder"[Title/Abstract] OR autism[Title/Abstract] OR ASD[Title/Abstract]) AND (intervention*[Title/Abstract] OR treatment[Title/Abstract] OR therapy[Title/Abstract] OR "parent-mediated"[Title/Abstract])',
    '("autism spectrum disorder"[Title/Abstract] OR autism[Title/Abstract] OR ASD[Title/Abstract]) AND (EEG[Title/Abstract] OR ERP[Title/Abstract] OR fMRI[Title/Abstract] OR "eye tracking"[Title/Abstract] OR biomarker*[Title/Abstract])',
    '("autism spectrum disorder"[Title/Abstract] OR autism[Title/Abstract] OR ASD[Title/Abstract]) AND (genetic*[Title/Abstract] OR genomic*[Title/Abstract] OR transcriptomic*[Title/Abstract] OR epigenetic*[Title/Abstract])',
    '("autism spectrum disorder"[Title/Abstract] OR autism[Title/Abstract] OR ASD[Title/Abstract]) AND ("systematic review"[Title/Abstract] OR "meta-analysis"[Publication Type] OR meta-analysis[Title/Abstract])',
    '("autism spectrum disorder"[Title/Abstract] OR autism[Title/Abstract] OR ASD[Title/Abstract]) AND (diagnos*[Title/Abstract] OR assess*[Title/Abstract]) AND (clinic*[Title/Abstract] OR patient*[Title/Abstract])',
]

HEADERS = {"User-Agent": "AutismBrainBot/1.0 (research aggregator)"}


def build_query(days: int = 7, max_journals: int = 12) -> str:
    journal_part = " OR ".join([f'"{j}"[Journal]' for j in JOURNALS[:max_journals]])
    lookback = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y/%m/%d")
    date_part = f'"{lookback}"[Date - Publication] : "3000"[Date - Publication]'

    query = f"({journal_part}) AND {date_part}"
    return query


def build_topic_queries(days: int = 7) -> list[str]:
    lookback = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y/%m/%d")
    date_part = f'"{lookback}"[Date - Publication] : "3000"[Date - Publication]'
    queries = []
    for q in SEARCH_QUERIES:
        queries.append(f"{q} AND {date_part}")
    return queries


def search_papers(query: str, retmax: int = 20) -> list[str]:
    params = (
        f"?db=pubmed&term={quote_plus(query)}&retmax={retmax}&sort=date&retmode=json"
    )
    url = PUBMED_SEARCH + params
    try:
        req = Request(url, headers=HEADERS)
        with urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
        return data.get("esearchresult", {}).get("idlist", [])
    except Exception as e:
        print(f"[ERROR] PubMed search failed: {e}", file=sys.stderr)
        return []


def fetch_details(pmids: list[str]) -> list[dict]:
    if not pmids:
        return []
    ids = ",".join(pmids)
    params = f"?db=pubmed&id={ids}&retmode=xml"
    url = PUBMED_FETCH + params
    try:
        req = Request(url, headers=HEADERS)
        with urlopen(req, timeout=60) as resp:
            xml_data = resp.read().decode()
    except Exception as e:
        print(f"[ERROR] PubMed fetch failed: {e}", file=sys.stderr)
        return []

    papers = []
    try:
        root = ET.fromstring(xml_data)
        for article in root.findall(".//PubmedArticle"):
            medline = article.find(".//MedlineCitation")
            art = medline.find(".//Article") if medline else None
            if art is None:
                continue

            title_el = art.find(".//ArticleTitle")
            title = (
                (title_el.text or "").strip()
                if title_el is not None and title_el.text
                else ""
            )

            abstract_parts = []
            for abs_el in art.findall(".//Abstract/AbstractText"):
                label = abs_el.get("Label", "")
                text = "".join(abs_el.itertext()).strip()
                if label and text:
                    abstract_parts.append(f"{label}: {text}")
                elif text:
                    abstract_parts.append(text)
            abstract = " ".join(abstract_parts)[:2000]

            journal_el = art.find(".//Journal/Title")
            journal = (
                (journal_el.text or "").strip()
                if journal_el is not None and journal_el.text
                else ""
            )

            pub_date = art.find(".//PubDate")
            date_str = ""
            if pub_date is not None:
                year = pub_date.findtext("Year", "")
                month = pub_date.findtext("Month", "")
                day = pub_date.findtext("Day", "")
                parts = [p for p in [year, month, day] if p]
                date_str = " ".join(parts)

            pmid_el = medline.find(".//PMID")
            pmid = pmid_el.text if pmid_el is not None else ""
            link = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else ""

            keywords = []
            for kw in medline.findall(".//KeywordList/Keyword"):
                if kw.text:
                    keywords.append(kw.text.strip())

            papers.append(
                {
                    "pmid": pmid,
                    "title": title,
                    "journal": journal,
                    "date": date_str,
                    "abstract": abstract,
                    "url": link,
                    "keywords": keywords,
                }
            )
    except ET.ParseError as e:
        print(f"[ERROR] XML parse failed: {e}", file=sys.stderr)

    return papers


def main():
    parser = argparse.ArgumentParser(description="Fetch autism papers from PubMed")
    parser.add_argument("--days", type=int, default=7, help="Lookback days")
    parser.add_argument("--max-papers", type=int, default=40, help="Max papers to fetch")
    parser.add_argument("--output", default="-", help="Output file (- for stdout)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    all_pmids = set()

    journal_query = build_query(days=args.days)
    print(f"[INFO] Searching by journal filter...", file=sys.stderr)
    pmids = search_papers(journal_query, retmax=args.max_papers)
    all_pmids.update(pmids)
    print(f"[INFO] Journal search found {len(pmids)} papers", file=sys.stderr)

    topic_queries = build_topic_queries(days=args.days)
    for i, tq in enumerate(topic_queries):
        print(f"[INFO] Topic query {i+1}/{len(topic_queries)}...", file=sys.stderr)
        pmids = search_papers(tq, retmax=10)
        all_pmids.update(pmids)

    pmid_list = list(all_pmids)
    print(f"[INFO] Total unique PMIDs: {len(pmid_list)}", file=sys.stderr)

    if not pmid_list:
        print("NO_CONTENT", file=sys.stderr)
        if args.json:
            output_data = {
                "date": datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d"),
                "count": 0,
                "papers": [],
            }
            out_str = json.dumps(output_data, ensure_ascii=False, indent=2)
            if args.output == "-":
                print(out_str)
            else:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(out_str)
        return

    pmid_list = pmid_list[: args.max_papers]
    papers = fetch_details(pmid_list)
    print(f"[INFO] Fetched details for {len(papers)} papers", file=sys.stderr)

    output_data = {
        "date": datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d"),
        "count": len(papers),
        "papers": papers,
    }

    out_str = json.dumps(output_data, ensure_ascii=False, indent=2)

    if args.output == "-":
        print(out_str)
    else:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out_str)
        print(f"[INFO] Saved to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
