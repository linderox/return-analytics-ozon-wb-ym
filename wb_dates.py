#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
returns/wb_dates.py

Сравнение количества возвратов по датам из трёх источников:
  1. GS CSV          — wb-returns-google-sheet.csv
  2. Маркетплейс CSV — wb_returns_report_marketplace.csv (из XLSX кабинета WB)
  3. API WB          — /api/v1/analytics/goods-return (30 дней)

Фильтр (как в wb_returns_fashion.gs): status == "Выдано"

Usage:
    python returns/wb_dates.py [--days 60]
"""

import argparse
import csv
import json
import os
from collections import defaultdict
from datetime import datetime, timedelta, timezone

import requests

RETURNS_DIR = os.path.dirname(os.path.abspath(__file__))

GS_TOKEN = (
    "eyJhbGciOiJFUzI1NiIsImtpZCI6IjIwMjYwMzAydjEiLCJ0eXAiOiJKV1QifQ.eyJhY2MiOjMsImVudCI6MSwiZXhwIjoxNzk4MDIwOTEyLCJmb3IiOiJzZWxmIiwiaWQiOiIwMTllZjY4ZC0zZGM5LTczMGMtYjU4MS00MTdmYjg4YzY5MTAiLCJpaWQiOjI2Njk5MDU3LCJvaWQiOjE1ODgxNiwicyI6MTA3Mzc0MzkwOCwic2lkIjoiNTgwMjQ2OGYtZDQ3NS00M2ZmLTgxMjAtYzFlMTY2MTdkMmI3IiwidCI6ZmFsc2UsInVpZCI6MjY2OTkwNTd9.FjhUt0FV9yIzI-YYkCTVT_5iijp_FE6g0FcaNkH8bkr4gYzVC78Gl2nCTtOu2GjWGgX6M7aHsyLTAXjgIhmeuA"
)

WB_URL = "https://seller-analytics-api.wildberries.ru/api/v1/analytics/goods-return"
STATUS_FILTER = "Выдано"


def read_csv(path):
    if not os.path.exists(path):
        return [], []
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    return (rows[0] if rows else []), (rows[1:] if len(rows) > 1 else [])


def load_gs_csv():
    """
    GS CSV: col 1 = "Дата заказа на возврат" (YYYY-MM-DD).
    Данные уже отфильтрованы скриптом GS (только "Выдано").
    """
    path = os.path.join(RETURNS_DIR, "wb-returns-google-sheet.csv")
    _, rows = read_csv(path)
    counts = defaultdict(int)
    for r in rows:
        d = r[1][:10] if len(r) > 1 and r[1] else ""
        if d >= "2020":
            counts[d] += 1
    return counts, len(rows), path


def load_marketplace_csv():
    """
    Маркетплейс CSV (конвертирован из XLSX кабинета WB).
    Двойной заголовок: строка 0 — группы, строка 1 — подзаголовки, строка 2+ — данные.
    col 7  = статус ("Выдано" / другие)
    col 12 = "Дата заказа" (YYYY-MM-DD)
    """
    path = os.path.join(RETURNS_DIR, "wb_returns_report_marketplace.csv")
    _, all_rows = read_csv(path)
    data_rows = all_rows[1:]  # пропускаем строку подзаголовков

    counts = defaultdict(int)
    skipped_status = 0
    for r in data_rows:
        status = r[7] if len(r) > 7 else ""
        if status != STATUS_FILTER:
            skipped_status += 1
            continue
        d = r[12][:10] if len(r) > 12 and r[12] else ""
        if d >= "2020":
            counts[d] += 1

    total_filtered = sum(counts.values())
    return counts, total_filtered, skipped_status, path


def fetch_api(days):
    today = datetime.now(tz=timezone.utc)
    past = today - timedelta(days=days)
    url = f"{WB_URL}?dateFrom={past.strftime('%Y-%m-%d')}&dateTo={today.strftime('%Y-%m-%d')}"
    try:
        resp = requests.get(url, headers={"Authorization": GS_TOKEN}, timeout=30)
    except Exception as e:
        return None, f"Ошибка соединения: {e}"

    if resp.status_code == 429:
        return None, "HTTP 429 — Rate limit WB. Подождите 60 с и повторите."
    if resp.status_code != 200:
        return None, f"HTTP {resp.status_code}: {resp.text[:300]}"

    try:
        data = resp.json()
    except Exception as e:
        return None, f"Ошибка парсинга JSON: {e}"

    records = data if isinstance(data, list) else (data.get("report") or [])
    filtered = [r for r in records if r.get("status") == STATUS_FILTER]

    counts = defaultdict(int)
    for r in filtered:
        d = (r.get("orderDt") or "")[:10]
        if d >= "2020":
            counts[d] += 1
    return counts, None


def print_table(gs, mp, api, api_err, days):
    all_dates = sorted(set(gs) | set(mp) | (set(api) if api else set()))

    H_DATE = "Дата"
    H_GS   = "GS CSV"
    H_MP   = "Маркетплейс"
    H_API  = f"API ({days}д)"
    H_DIFF = "Разница GS/API"

    W = [12, 10, 14, 12, 16]
    line = f"{'─'*W[0]}─{'─'*W[1]}─{'─'*W[2]}─{'─'*W[3]}─{'─'*W[4]}"

    print()
    print(f"WildBerries — количество возвратов по датам  (фильтр: «{STATUS_FILTER}»)")
    print("═" * len(line))
    print(f"{H_DATE:<{W[0]}} {H_GS:>{W[1]}} {H_MP:>{W[2]}} {H_API:>{W[3]}} {H_DIFF:>{W[4]}}")
    print(line)

    gs_tot = mp_tot = api_tot = 0
    for d in all_dates:
        g = gs.get(d, 0)
        m = mp.get(d, 0)
        a = api.get(d) if api else None
        a_s = str(a) if a is not None else "—"
        diff_s = str(g - a) if a is not None else "—"
        gs_tot += g
        mp_tot += m
        if a:
            api_tot += a
        print(f"{d:<{W[0]}} {g:>{W[1]}} {m:>{W[2]}} {a_s:>{W[3]}} {diff_s:>{W[4]}}")

    print(line)
    api_tot_s = str(api_tot) if not api_err else "ERR"
    print(f"{'ИТОГО':<{W[0]}} {gs_tot:>{W[1]}} {mp_tot:>{W[2]}} {api_tot_s:>{W[3]}}")

    if api_err:
        print(f"\n[ОШИБКА API] {api_err}")
    print()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=30, help="Окно запроса к API (дней)")
    args = parser.parse_args()

    print(f"[1/3] GS CSV...")
    gs, gs_total, gs_path = load_gs_csv()
    print(f"      {gs_total} строк | {len(gs)} дат | {os.path.basename(gs_path)}")

    print(f"[2/3] Маркетплейс CSV...")
    mp, mp_total, mp_skip, mp_path = load_marketplace_csv()
    print(f"      {mp_total} строк после фильтра | {len(mp)} дат | пропущено (не «{STATUS_FILTER}»): {mp_skip}")

    print(f"[3/3] API WB ({args.days} дней)...")
    api, api_err = fetch_api(args.days)
    if api_err:
        print(f"      [ОШИБКА] {api_err}")
    else:
        print(f"      {sum(api.values())} записей после фильтра | {len(api)} дат")

    print_table(gs, mp, api, api_err, args.days)


if __name__ == "__main__":
    main()
