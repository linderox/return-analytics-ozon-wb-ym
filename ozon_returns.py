#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
returns/ozon_returns.py

Debug script: Ozon returns — mirrors ozon_returns_fashion.gs logic.
Checks token, fetches current API data, compares with CSV/XLSX snapshots.

Usage:
    python returns/ozon_returns.py [--shop shop_id1]
    python returns/ozon_returns.py --client-id 465010 --api-key d704b9fb-...
"""
import argparse
import csv
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone

import requests

RETURNS_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(RETURNS_DIR, "ozon_returns_gs.csv")
XLSX_GLOB = "ozon_returns__report_marketplace"

OZON_RETURNS_URL = "https://api-seller.ozon.ru/v1/returns/list"
CLIENT_SECRET_OZON = "1d3af06e-b862-4830-8ade-7880fa1ca8ae"	
CLIENT_ID_OZON = "141168"

def convert_xlsx_to_csv(xlsx_path: str) -> str:
    """Convert XLSX to a permanent companion CSV next to the source file."""
    csv_path = os.path.splitext(xlsx_path)[0] + ".csv"
    print(f"  Converting {os.path.basename(xlsx_path)} → {os.path.basename(csv_path)}")
    subprocess.run(["xlsx2csv", xlsx_path, csv_path], check=True, capture_output=True)
    return csv_path


def convert_all_xlsx():
    """Pre-convert all XLSX files in returns/ to CSV before analysis."""
    print("=" * 60)
    print("[PRE-STEP] Converting all XLSX files in returns/ to CSV")
    converted = []
    for fname in sorted(os.listdir(RETURNS_DIR)):
        if fname.endswith(".xlsx"):
            xlsx_path = os.path.join(RETURNS_DIR, fname)
            try:
                csv_path = convert_xlsx_to_csv(xlsx_path)
                converted.append(csv_path)
            except Exception as e:
                print(f"  [WARNING] Could not convert {fname}: {e}")
    if not converted:
        print("  No XLSX files found.")
    print()
    return converted


def read_csv_file(path: str):
    if not os.path.exists(path):
        return [], []
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    return (rows[0] if rows else []), (rows[1:] if len(rows) > 1 else [])


def load_csv_snapshot(path):
    if not os.path.exists(path):
        return [], []
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    return (rows[0] if rows else []), (rows[1:] if len(rows) > 1 else [])


def fetch_ozon_returns(client_id, api_key, days):
    now = datetime.now(tz=timezone.utc)
    time_from = (now - timedelta(days=days)).isoformat()
    time_to = now.isoformat()

    all_returns = []
    last_id = 0
    has_next = True

    while has_next:
        body = {
            "filter": {
                "logistic_return_date": {
                    "time_from": time_from,
                    "time_to": time_to,
                }
            },
            "limit": 500,
            "last_id": last_id,
        }
        try:
            resp = requests.post(
                OZON_RETURNS_URL,
                json=body,
                headers={"Client-Id": str(client_id), "Api-Key": api_key},
                timeout=30,
            )
        except Exception as e:
            return None, 0, str(e)

        if resp.status_code != 200:
            return None, resp.status_code, resp.text

        data = resp.json()
        returns = data.get("returns") or []
        if not returns:
            break

        all_returns.extend(returns)
        has_next = bool(data.get("has_next"))
        last_id = data.get("last_id") or (returns[-1].get("id", 0) if returns else 0)

    return all_returns, 200, None


def find_xlsx():
    for fname in os.listdir(RETURNS_DIR):
        if XLSX_GLOB in fname and fname.endswith(".xlsx"):
            return os.path.join(RETURNS_DIR, fname)
    return None



def main():
    parser = argparse.ArgumentParser(description="Debug Ozon returns API")
    parser.add_argument("--client-id", help="Override: Ozon seller_client_id")
    parser.add_argument("--api-key", help="Override: Ozon seller_api_key")
    args = parser.parse_args()

    convert_all_xlsx()

    if args.client_id and args.api_key:
        client_id = args.client_id
        api_key = args.api_key
        label = f"--client-id={client_id}"
    else:
        client_id = CLIENT_ID_OZON
        api_key = CLIENT_SECRET_OZON
        label = f"CLIENT_ID_OZON={client_id}"

    print(f"[USING SHOP] {label}  client_id={client_id}")
    print()

    # CSV snapshot
    print("=" * 60)
    print("[CSV SNAPSHOT] ozon_returns_gs.csv")
    headers, rows = read_csv_file(CSV_PATH)
    existing_postings = set()
    if rows and headers:
        print(f"  Rows (excl. header): {len(rows)}")
        date_col = 0   # Дата добавления
        post_col = 1   # Номер отправления
        stat_col = 5   # Статус
        dates = sorted(r[date_col] for r in rows if len(r) > date_col and r[date_col])
        print(f"  Date range: {dates[0][:10] if dates else '?'} → {dates[-1][:10] if dates else '?'}")
        existing_postings = {r[post_col] for r in rows if len(r) > post_col and r[post_col]}
        print(f"  Unique posting numbers: {len(existing_postings)}")
        statuses: dict = {}
        for r in rows:
            s = r[stat_col] if len(r) > stat_col else ""
            statuses[s] = statuses.get(s, 0) + 1
        top = sorted(statuses.items(), key=lambda x: -x[1])[:8]
        print(f"  Status distribution: {dict(top)}")
    else:
        print("  [WARNING] CSV not found or empty")
    print()

    # XLSX snapshot (reads the pre-converted CSV)
    print("=" * 60)
    print("[XLSX SNAPSHOT] ozon_returns__report_marketplace_*.xlsx → .csv")
    xlsx_path = find_xlsx()
    if xlsx_path:
        companion_csv = os.path.splitext(xlsx_path)[0] + ".csv"
        print(f"  File: {os.path.basename(xlsx_path)}")
        if os.path.exists(companion_csv):
            _, xlsx_rows = read_csv_file(companion_csv)
            print(f"  Rows: {len(xlsx_rows)} data rows")
        else:
            print("  [WARNING] Companion CSV not found (conversion may have failed)")
    else:
        print("  [WARNING] XLSX not found in returns/")
    print()

    # API calls — two window sizes
    for days, label_win in [(12, "12-day (matches .gs)"), (60, "60-day (extended)")]:
        print("=" * 60)
        print(f"[API CALL — {label_win}]")
        result, status_code, error = fetch_ozon_returns(client_id, api_key, days)

        if status_code != 200:
            print(f"  HTTP {status_code}")
            if error:
                print(f"  Response: {error[:400]}")
            print()
            continue

        if not result:
            print(f"  HTTP 200 — 0 records returned")
            print()
            continue

        print(f"  HTTP 200 — {len(result)} records")

        # Split by status
        received = [r for r in result if r.get("schema") == "ReceivedBySeller"]
        arrived  = [r for r in result if r.get("schema") == "ArrivedAtReturnPlace"]
        other    = [r for r in result if r.get("schema") not in ("ReceivedBySeller", "ArrivedAtReturnPlace")]

        print(f"  ReceivedBySeller      (есть received_at): {len(received)}")
        print(f"  ArrivedAtReturnPlace  (нет received_at):  {len(arrived)}")
        if other:
            print(f"  Прочие статусы:                          {len(other)}")

        # Date range — только ReceivedBySeller имеет осмысленный received_at
        rdates = sorted(r.get("received_at", "") for r in received if r.get("received_at"))
        if rdates:
            print(f"  received_at range: {rdates[0][:10]} → {rdates[-1][:10]}")
        elif received:
            print(f"  [WARN] ReceivedBySeller есть, но received_at пуст во всех записях")

        # All statuses
        status_cnt: dict = {}
        for r in result:
            schema = r.get("schema", "")
            sname = (r.get("visual") or {}).get("status_name", "?")
            key = f"[{schema}] {sname}" if schema else sname
            status_cnt[key] = status_cnt.get(key, 0) + 1
        print(f"  Statuses: {dict(sorted(status_cnt.items(), key=lambda x: -x[1]))}")

        # Overlap
        api_postings = {r.get("posting_number", "") for r in result if r.get("posting_number")}
        new_postings = api_postings - existing_postings
        print(f"  Postings from API: {len(api_postings)}")
        print(f"  Already in CSV: {len(api_postings & existing_postings)}")
        print(f"  NEW (not in CSV): {len(new_postings)}")
        if new_postings:
            print(f"  Sample new postings: {list(new_postings)[:5]}")

        # Sample record — предпочитаем ReceivedBySeller (у него есть received_at)
        sample = received[0] if received else result[0]
        sample_label = "ReceivedBySeller" if received else result[0].get("schema", "first")
        print(f"  Sample record ({sample_label}):")
        print("    " + json.dumps(sample, ensure_ascii=False, indent=2).replace("\n", "\n    "))
        print()

    print("=" * 60)
    print("[GAP DIAGNOSIS]")
    print("  HTTP != 200  → credentials in GSheet 'Настройка' tab are wrong/expired")
    print("  0 records    → no returns in that window (try --shop with wider range)")
    print("  NEW postings → GS script stopped triggering (check Apps Script triggers)")
    print("  All in CSV   → deduplication blocks writes; check last date in CSV matches reality")


if __name__ == "__main__":
    main()
