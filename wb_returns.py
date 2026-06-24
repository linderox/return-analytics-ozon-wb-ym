#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
returns/wb_returns.py

Debug script: WB returns — mirrors wb_returns_fashion.gs logic.
Decodes JWT expiry, fetches current API data, compares with CSV/XLSX snapshots.

Usage:
    python returns/wb_returns.py
"""
import base64
import csv
import json
import os
import subprocess
from datetime import datetime, timedelta, timezone

import requests

RETURNS_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(RETURNS_DIR, "wb-returns-google-sheet.csv")
XLSX_PATH = os.path.join(RETURNS_DIR, "wb_returns_report_marketplace.xlsx")

# Token from wb_returns_fashion.gs (fashion shop, oid=158816)
GS_TOKEN = (
    "eyJhbGciOiJFUzI1NiIsImtpZCI6IjIwMjYwMzAydjEiLCJ0eXAiOiJKV1QifQ"
    ".eyJhY2MiOjEsImVudCI6MSwiZXhwIjoxNzkxMDk1MTEzLCJpZCI6IjAxOWQ1OWJkLWVmZTAt"
    "N2JiNC1hMWQ0LWM3YTkzM2M3MTY0ZiIsImlpZCI6MjY2OTkwNTcsIm9pZCI6MTU4ODE2LCJzIj"
    "oxMDczNzQ0OTU4LCJzaWQiOiI1ODAyNDY4Zi1kNDc1LTQzZmYtODEyMC1jMWUxNjYxN2QyYjci"
    "LCJ0IjpmYWxzZSwidWlkIjoyNjY5OTA1N30"
    ".Yw7aQjoTpsBkGtKk0EkFcKdEq4lf0IL-UJeNZg6t5vFCdE4rkGXnL_Z7-31FzEzdxWMMcawy"
    "HfDxA11W-9GQ9g"
)

WB_RETURNS_URL = "https://seller-analytics-api.wildberries.ru/api/v1/analytics/goods-return"
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
# JWT decode
# ---------------------------------------------------------------------------

def decode_jwt(token: str) -> dict:
    parts = token.replace("\n", "").replace(" ", "").split(".")
    if len(parts) < 2:
        return {"_error": "not a JWT"}
    payload = parts[1]
    pad = 4 - len(payload) % 4
    if pad != 4:
        payload += "=" * pad
    try:
        data = json.loads(base64.urlsafe_b64decode(payload).decode("utf-8"))
        exp_ts = data.get("exp")
        if exp_ts:
            exp_dt = datetime.fromtimestamp(exp_ts, tz=timezone.utc)
            data["_exp_human"] = exp_dt.strftime("%Y-%m-%d %H:%M UTC")
            data["_days_remaining"] = (exp_dt - datetime.now(tz=timezone.utc)).days
        return data
    except Exception as e:
        return {"_error": str(e)}


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

def fetch_wb_returns(token: str, days: int):
    today = datetime.now(tz=timezone.utc)
    past = today - timedelta(days=days)
    url = (
        f"{WB_RETURNS_URL}"
        f"?dateFrom={past.strftime('%Y-%m-%d')}&dateTo={today.strftime('%Y-%m-%d')}"
    )
    try:
        resp = requests.get(url, headers={"Authorization": token}, timeout=30)
        return resp.status_code, resp.text
    except Exception as e:
        return 0, str(e)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    convert_all_xlsx()

    # Token check
    print("=" * 60)
    print("[TOKEN CHECK] wb_returns_fashion.gs JWT")
    jwt = decode_jwt(GS_TOKEN)
    if "_error" in jwt:
        print(f"  [ERROR] {jwt['_error']}")
    else:
        print(f"  oid (shop ID):   {jwt.get('oid')}")
        print(f"  acc (scope):     {jwt.get('acc')}  (1=analytics, 3=general/content)")
        print(f"  Expires:         {jwt.get('_exp_human', '?')}")
        days_left = jwt.get("_days_remaining", -999)
        if days_left <= 0:
            print(f"  [WARNING] TOKEN EXPIRED {abs(days_left)} days ago!")
        else:
            print(f"  Days remaining:  {days_left}  [OK]")
    print()

    # CSV snapshot
    print("=" * 60)
    print("[CSV SNAPSHOT] wb-returns-google-sheet.csv")
    headers, rows = read_csv(CSV_PATH)
    existing_srids: set = set()
    if rows and headers:
        print(f"  Rows (excl. header): {len(rows)}")
        srid_col, date_col, status_col = 0, 1, 10
        existing_srids = {r[srid_col] for r in rows if len(r) > srid_col and r[srid_col]}
        dates = sorted(r[date_col][:10] for r in rows if len(r) > date_col and r[date_col])
        print(f"  Date range: {dates[0] if dates else '?'} → {dates[-1] if dates else '?'}")
        print(f"  Unique srids: {len(existing_srids)}")
        status_cnt: dict = {}
        for r in rows:
            s = r[status_col] if len(r) > status_col else ""
            status_cnt[s] = status_cnt.get(s, 0) + 1
        print(f"  Status distribution: {dict(sorted(status_cnt.items(), key=lambda x: -x[1]))}")
    else:
        print("  [WARNING] CSV not found or empty")
    print()

    # XLSX snapshot (reads the pre-converted companion CSV)
    print("=" * 60)
    print("[XLSX SNAPSHOT] wb_returns_report_marketplace.xlsx → .csv")
    companion = os.path.splitext(XLSX_PATH)[0] + ".csv"
    if os.path.exists(companion):
        _, xlsx_rows = read_csv(companion)
        print(f"  Rows: {len(xlsx_rows)} data rows")
        if xlsx_rows:
            print(f"  Columns (first 5): {xlsx_rows[0][:5] if xlsx_rows else []}")
        dates_x = sorted(r[1][:10] for r in xlsx_rows if len(r) > 1 and r[1] and len(r[1]) >= 10 and r[1][4] == "-")
        if dates_x:
            print(f"  Date range: {dates_x[0]} → {dates_x[-1]}")
    else:
        print(f"  [WARNING] Companion CSV not found ({os.path.basename(companion)})")
    print()

    # API call
    print("=" * 60)
    print(f"[API CALL] {DAYS_TO_FETCH}-day window  oid={jwt.get('oid', '?')}")
    status_code, response_text = fetch_wb_returns(GS_TOKEN, DAYS_TO_FETCH)
    print(f"  HTTP Status: {status_code}")

    if status_code == 429:
        print(f"  [RATE LIMIT 429] WB is throttling — wait ~60s and retry")
        print(f"  Response: {response_text[:300]}")
        print()
        return

    if status_code != 200:
        print(f"  Response: {response_text[:500]}")
        print()
        print("=" * 60)
        print("[GAP DIAGNOSIS]")
        if status_code == 401:
            print("  HTTP 401 → Token invalid or revoked. Generate a new WB Analytics token.")
        elif status_code == 403:
            print("  HTTP 403 → Token has wrong scope (need analytics permission, acc=1)")
        else:
            print(f"  HTTP {status_code} → Unexpected error, see response above")
        return

    try:
        data = json.loads(response_text)
    except Exception as e:
        print(f"  [ERROR] JSON parse failed: {e}")
        print(f"  Raw: {response_text[:300]}")
        return

    if isinstance(data, list):
        all_records = data
    elif isinstance(data, dict):
        all_records = data.get("report") or data.get("data") or data.get("returns") or []
        if not all_records:
            print(f"  [WARNING] Unexpected response keys: {list(data.keys())}")
            print(f"  Full response: {response_text[:800]}")
    else:
        all_records = []
        print(f"  [WARNING] Unexpected type: {type(data)}")

    print(f"  Total records (no filter): {len(all_records)}")
    print()

    if all_records:
        status_cnt2: dict = {}
        for r in all_records:
            s = r.get("status", "")
            status_cnt2[s] = status_cnt2.get(s, 0) + 1
        print("[ALL STATUSES from API]")
        for s, cnt in sorted(status_cnt2.items(), key=lambda x: -x[1]):
            marker = "  ← FILTER TARGET" if s == "Выдано" else ""
            print(f"  '{s}': {cnt}{marker}")
        print()

        filtered = [r for r in all_records if r.get("status") == "Выдано"]
        print(f"  Records passing filter (status='Выдано'): {len(filtered)}")
        print()

        api_srids = {r.get("srid", "") for r in all_records if r.get("srid")}
        new_srids = api_srids - existing_srids
        print("[OVERLAP]")
        print(f"  srids from API: {len(api_srids)}")
        print(f"  Already in CSV: {len(api_srids & existing_srids)}")
        print(f"  NEW (not in CSV): {len(new_srids)}")
        if new_srids:
            print(f"  Sample new: {list(new_srids)[:5]}")
        print()

        print("[SAMPLE] First raw record:")
        print("  " + json.dumps(all_records[0], ensure_ascii=False, indent=2)[:600].replace("\n", "\n  "))
    else:
        print("  [RESULT] 0 records from API")
        print("  Trying 60-day window...")
        sc2, rt2 = fetch_wb_returns(GS_TOKEN, 60)
        if sc2 == 200:
            try:
                d2 = json.loads(rt2)
                recs2 = d2 if isinstance(d2, list) else (d2.get("report") or [])
                print(f"  60-day result: {len(recs2)} records")
            except Exception:
                pass

    print()
    print("=" * 60)
    print("[GAP DIAGNOSIS]")
    print("  HTTP 429      → rate-limited; retry in ~60s (token is valid)")
    print("  HTTP 401/403  → token invalid/revoked or wrong scope (need acc=1 analytics)")
    print("  0 records     → no returns for oid=158816 shop in 30d window")
    print("  0 'Выдано'    → status string changed; check ALL STATUSES above, update .gs filter")
    print("  NEW srids     → GS stopped triggering; check Apps Script scheduled triggers")
    print("  All in CSV    → deduplication blocks; check last srid date in CSV")


if __name__ == "__main__":
    main()
