#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
returns/ym_returns.py

Debug script: Yandex Market returns — mirrors ym_returns_fashion.gs logic.
Tests API key, fetches current data with pagination, compares with CSV/XLSX snapshots.

Usage:
    python returns/ym_returns.py
"""
import csv
import json
import os
import subprocess
from datetime import datetime, timedelta, timezone

import requests

RETURNS_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(RETURNS_DIR, "ym_returns_google_sheet.csv")
XLSX_PATH = os.path.join(RETURNS_DIR, "ym_united_returns_marketplae_23-03-2026_23-06-2026.xlsx")

# Credentials from ym_returns_fashion.gs
GS_API_KEY = "ACMA:fyrpztZMH8WM7z76istlJaxcTfi3jRbfXXOaAJnL:b7f4f021"
GS_CAMPAIGN_ID = "22209372"

YM_BASE_URL = "https://api.partner.market.yandex.ru"
DAYS_TO_FETCH = 30


# ---------------------------------------------------------------------------
# XLSX → CSV conversion (pre-step)
# ---------------------------------------------------------------------------

def convert_xlsx_to_csv(xlsx_path: str) -> str:
    csv_path = os.path.splitext(xlsx_path)[0] + ".csv"
    print(f"  Converting {os.path.basename(xlsx_path)} → {os.path.basename(csv_path)}")
    subprocess.run(["xlsx2csv", xlsx_path, csv_path], check=True, capture_output=True)
    return csv_path


def convert_all_xlsx():
    print("=" * 60)
    print("[PRE-STEP] Converting all XLSX files in returns/ to CSV")
    converted = []
    for fname in sorted(os.listdir(RETURNS_DIR)):
        if fname.endswith(".xlsx"):
            try:
                csv_path = convert_xlsx_to_csv(os.path.join(RETURNS_DIR, fname))
                converted.append(csv_path)
            except Exception as e:
                print(f"  [WARNING] Could not convert {fname}: {e}")
    if not converted:
        print("  No XLSX files found.")
    print()


def read_csv(path: str):
    if not os.path.exists(path):
        return [], []
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    return (rows[0] if rows else []), (rows[1:] if len(rows) > 1 else [])


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

def fetch_ym_returns(api_key: str, campaign_id: str, days: int):
    today = datetime.now(tz=timezone.utc)
    past = today - timedelta(days=days)
    to_date = today.strftime("%Y-%m-%d")
    from_date = past.strftime("%Y-%m-%d")

    all_returns = []
    page_token = ""
    page_count = 0

    while True:
        url = (
            f"{YM_BASE_URL}/v2/campaigns/{campaign_id}/returns"
            f"?fromDate={from_date}&toDate={to_date}&limit=100"
        )
        if page_token:
            url += f"&pageToken={page_token}"

        try:
            resp = requests.get(url, headers={"Api-Key": api_key}, timeout=30)
        except Exception as e:
            return None, 0, str(e)

        if resp.status_code != 200:
            return None, resp.status_code, resp.text

        try:
            data = resp.json()
        except Exception as e:
            return None, resp.status_code, f"JSON parse error: {e}"

        result = data.get("result") or {}
        page_returns = result.get("returns") or []
        all_returns.extend(page_returns)
        page_count += 1

        paging = result.get("paging") or {}
        page_token = paging.get("nextPageToken", "")
        if not page_token or page_count >= 50:
            break

    return all_returns, 200, None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    convert_all_xlsx()

    print("=" * 60)
    print("[CREDENTIALS] ym_returns_fashion.gs")
    print(f"  API_KEY:     {GS_API_KEY}")
    print(f"  CAMPAIGN_ID: {GS_CAMPAIGN_ID}")
    print()

    # CSV snapshot
    print("=" * 60)
    print("[CSV SNAPSHOT] ym_returns_google_sheet.csv")
    headers, rows = read_csv(CSV_PATH)
    existing_ids: set = set()
    if rows and headers:
        print(f"  Rows (excl. header): {len(rows)}")
        id_col, date_col, ship_col, type_col = 0, 5, 3, 2
        existing_ids = {r[id_col] for r in rows if len(r) > id_col and r[id_col]}
        dates = sorted(r[date_col][:10] for r in rows if len(r) > date_col and r[date_col])
        print(f"  Date range: {dates[0] if dates else '?'} → {dates[-1] if dates else '?'}")
        print(f"  Unique return IDs: {len(existing_ids)}")
        ship_cnt: dict = {}
        for r in rows:
            s = r[ship_col] if len(r) > ship_col else ""
            ship_cnt[s] = ship_cnt.get(s, 0) + 1
        print(f"  Shipment statuses in CSV: {dict(sorted(ship_cnt.items(), key=lambda x: -x[1]))}")
        type_cnt: dict = {}
        for r in rows:
            t = r[type_col] if len(r) > type_col else ""
            type_cnt[t] = type_cnt.get(t, 0) + 1
        print(f"  Return types in CSV: {dict(sorted(type_cnt.items(), key=lambda x: -x[1]))}")
    else:
        print("  [WARNING] CSV not found or empty")
    print()

    # XLSX snapshot (reads pre-converted companion CSV)
    print("=" * 60)
    print("[XLSX SNAPSHOT] ym_united_returns_marketplae_23-03-2026_23-06-2026.xlsx → .csv")
    companion = os.path.splitext(XLSX_PATH)[0] + ".csv"
    if os.path.exists(companion):
        _, xlsx_rows = read_csv(companion)
        print(f"  Rows: {len(xlsx_rows)} data rows")
        if xlsx_rows:
            print(f"  Columns (first 5): {xlsx_rows[0][:5]}")
        dates_x = sorted(
            r[5][:10] for r in xlsx_rows
            if len(r) > 5 and r[5] and len(r[5]) >= 10 and r[5][4] == "-"
        )
        if dates_x:
            print(f"  Date range: {dates_x[0]} → {dates_x[-1]}")
    else:
        print(f"  [WARNING] Companion CSV not found ({os.path.basename(companion)})")
    print()

    # API call
    print("=" * 60)
    print(f"[API CALL] campaign_id={GS_CAMPAIGN_ID}, {DAYS_TO_FETCH}-day window")
    result, status_code, error = fetch_ym_returns(GS_API_KEY, GS_CAMPAIGN_ID, DAYS_TO_FETCH)
    print(f"  HTTP Status: {status_code}")

    if status_code != 200:
        print(f"  Response: {error[:500] if error else ''}")
        print()
        print("=" * 60)
        print("[GAP DIAGNOSIS]")
        if status_code == 401:
            print("  HTTP 401 → API key invalid or revoked. Generate a new key in YM cabinet.")
        elif status_code == 403:
            print("  HTTP 403 → API key lacks permission or wrong campaign. Check CAMPAIGN_ID.")
        elif status_code == 404:
            print("  HTTP 404 → Campaign not found. CAMPAIGN_ID=22209372 may be wrong.")
        else:
            print(f"  HTTP {status_code} → Unexpected error, see response above")
        return

    if result is None:
        print("  [ERROR] Could not parse API response")
        return

    print(f"  Total records (no filter): {len(result)}")
    print()

    if result:
        ship_cnt2: dict = {}
        for r in result:
            s = r.get("shipmentStatus", "")
            ship_cnt2[s] = ship_cnt2.get(s, 0) + 1
        print("[ALL SHIPMENT STATUSES from API]")
        for s, cnt in sorted(ship_cnt2.items(), key=lambda x: -x[1]):
            marker = "  ← FILTER TARGET" if s == "PICKED" else ""
            print(f"  '{s}': {cnt}{marker}")
        print()

        type_cnt2: dict = {}
        for r in result:
            t = r.get("returnType", "")
            type_cnt2[t] = type_cnt2.get(t, 0) + 1
        print(f"  Return types: {dict(sorted(type_cnt2.items(), key=lambda x: -x[1]))}")
        print()

        filtered = [r for r in result if r.get("shipmentStatus") == "PICKED"]
        print(f"  Records passing filter (shipmentStatus='PICKED'): {len(filtered)}")
        print()

        api_ids = {str(r.get("id", "")) for r in result if r.get("id")}
        new_ids = api_ids - existing_ids
        print("[OVERLAP]")
        print(f"  Return IDs from API: {len(api_ids)}")
        print(f"  Already in CSV: {len(api_ids & existing_ids)}")
        print(f"  NEW (not in CSV): {len(new_ids)}")
        if new_ids:
            print(f"  Sample new IDs: {list(new_ids)[:5]}")
        print()

        ref_cnt: dict = {}
        for r in result:
            s = r.get("refundStatus", "")
            ref_cnt[s] = ref_cnt.get(s, 0) + 1
        print(f"  Refund statuses: {dict(sorted(ref_cnt.items(), key=lambda x: -x[1]))}")
        print()

        print("[SAMPLE] First raw record:")
        print("  " + json.dumps(result[0], ensure_ascii=False, indent=2)[:600].replace("\n", "\n  "))
    else:
        print("  [RESULT] 0 records in 30-day window. Trying 90-day...")
        r90, sc90, _ = fetch_ym_returns(GS_API_KEY, GS_CAMPAIGN_ID, 90)
        if sc90 == 200 and r90:
            print(f"  90-day result: {len(r90)} records found!")
            ship90: dict = {}
            for r in r90:
                s = r.get("shipmentStatus", "")
                ship90[s] = ship90.get(s, 0) + 1
            print(f"  Statuses in 90d: {ship90}")
        else:
            print("  90-day also returned 0 records")

    print()
    print("=" * 60)
    print("[GAP DIAGNOSIS]")
    print("  HTTP 401/403/404 → API key invalid, revoked, or wrong CAMPAIGN_ID")
    print("  0 records        → no returns for campaign 22209372 in that window")
    print("  0 'PICKED'       → status changed; check ALL STATUSES above, update .gs filter")
    print("  NEW IDs          → GS stopped triggering; check Apps Script scheduled triggers")
    print("  All IDs in CSV   → deduplication blocks; verify last date in CSV is current")


if __name__ == "__main__":
    main()
