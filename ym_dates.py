#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
returns/ym_dates.py

Сравнение количества возвратов по датам из трёх источников:
  1. GS CSV          — ym_returns_google_sheet.csv
  2. Маркетплейс CSV — ym_united_returns_*.csv (из XLSX кабинета ЯМ — сводный отчёт)
  3. API ЯМ          — /v2/campaigns/{id}/returns (30 дней)

Фильтр (как в ym_returns_fashion.gs): shipmentStatus == "PICKED"
Дата группировки: creationDate → колонка F "Дата создания" в GS CSV.

Usage:
    python returns/ym_dates.py [--days 60]
"""

import argparse
import csv
import glob
import json
import os
from collections import defaultdict
from datetime import datetime, timedelta, timezone

import requests

RETURNS_DIR = os.path.dirname(os.path.abspath(__file__))

GS_API_KEY    = "ACMA:fyrpztZMH8WM7z76istlJaxcTfi3jRbfXXOaAJnL:b7f4f021"
GS_CAMPAIGN_ID = "22209372"
YM_BASE_URL   = "https://api.partner.market.yandex.ru"
STATUS_FILTER = "PICKED"


def read_csv(path):
    if not os.path.exists(path):
        return [], []
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    return (rows[0] if rows else []), (rows[1:] if len(rows) > 1 else [])


def load_gs_csv():
    """
    GS CSV: col 5 = "Дата создания" (ISO datetime, например "2026-06-12T17:16:09.408+03:00").
    Данные уже отфильтрованы скриптом GS (только "PICKED").
    """
    path = os.path.join(RETURNS_DIR, "ym_returns_google_sheet.csv")
    _, rows = read_csv(path)
    counts = defaultdict(int)
    for r in rows:
        d = r[5][:10] if len(r) > 5 and r[5] else ""
        if d >= "2020":
            counts[d] += 1
    return counts, len(rows), path


def load_marketplace_csv():
    """
    Маркетплейс CSV (конвертирован из XLSX кабинета ЯМ).
    Файл — сводный отчёт, не построчные данные возвратов:
      строка 0 = название отчёта
      строка 1 = описание
      строки 2-4 = метаданные (ID, модели, магазины)
    Возвращает None как данные + пояснение.
    """
    pattern = os.path.join(RETURNS_DIR, "ym_united_returns_*.csv")
    files = sorted(glob.glob(pattern))
    if not files:
        return None, "файл не найден"

    path = files[-1]
    _, rows = read_csv(path)
    total_rows = len(rows)

    # Пытаемся найти строки с датами (ISO формат YYYY-MM-DD)
    counts = defaultdict(int)
    for r in rows:
        for cell in r:
            if cell and len(cell) >= 10 and cell[4] == "-" and cell[7] == "-":
                d = cell[:10]
                if d >= "2020":
                    counts[d] += 1
                    break

    if counts:
        note = f"сводный отчёт | {os.path.basename(path)} | найдено дат: {len(counts)}"
        return counts, note
    else:
        return None, f"сводный отчёт | {os.path.basename(path)} | построчное сравнение невозможно"


def fetch_api(days):
    today = datetime.now(tz=timezone.utc)
    past = today - timedelta(days=days)
    from_date = past.strftime("%Y-%m-%d")
    to_date = today.strftime("%Y-%m-%d")

    all_returns = []
    page_token = ""
    page_count = 0

    while True:
        url = (
            f"{YM_BASE_URL}/v2/campaigns/{GS_CAMPAIGN_ID}/returns"
            f"?fromDate={from_date}&toDate={to_date}&limit=100"
        )
        if page_token:
            url += f"&pageToken={page_token}"

        try:
            resp = requests.get(url, headers={"Api-Key": GS_API_KEY}, timeout=30)
        except Exception as e:
            return None, f"Ошибка соединения: {e}"

        if resp.status_code != 200:
            return None, f"HTTP {resp.status_code}: {resp.text[:300]}"

        try:
            data = resp.json()
        except Exception as e:
            return None, f"Ошибка парсинга JSON: {e}"

        result = data.get("result") or {}
        page_returns = result.get("returns") or []
        all_returns.extend(page_returns)
        page_count += 1

        paging = result.get("paging") or {}
        page_token = paging.get("nextPageToken", "")
        if not page_token or page_count >= 50:
            break

    filtered = [r for r in all_returns if r.get("shipmentStatus") == STATUS_FILTER]
    counts = defaultdict(int)
    for r in filtered:
        d = (r.get("creationDate") or "")[:10]
        if d >= "2020":
            counts[d] += 1
    return counts, None


def print_table(gs, mp, api, api_err, days, mp_note):
    has_mp = bool(mp)
    all_dates = sorted(set(gs) | (set(mp) if mp else set()) | (set(api) if api else set()))

    W = [12, 10, 14, 12, 16] if has_mp else [12, 10, 12, 16]
    line = "─" * (sum(W) + len(W) - 1)

    print()
    print(f"Яндекс Маркет — количество возвратов по датам  (фильтр: shipmentStatus = «{STATUS_FILTER}»)")
    if mp_note:
        print(f"  Маркетплейс CSV: {mp_note}")
    print("═" * len(line))

    if has_mp:
        print(f"{'Дата':<{W[0]}} {'GS CSV':>{W[1]}} {'Маркетплейс':>{W[2]}} {f'API ({days}д)':>{W[3]}} {'Разница GS/API':>{W[4]}}")
    else:
        print(f"{'Дата':<{W[0]}} {'GS CSV':>{W[1]}} {f'API ({days}д)':>{W[2]}} {'Разница GS/API':>{W[3]}}")
    print(line)

    gs_tot = mp_tot = api_tot = 0
    for d in all_dates:
        g = gs.get(d, 0)
        m = mp.get(d, 0) if mp else None
        a = api.get(d) if api else None
        a_s = str(a) if a is not None else "—"
        diff_s = str(g - a) if a is not None else "—"
        gs_tot += g
        if m is not None:
            mp_tot += m
        if a:
            api_tot += a

        if has_mp:
            m_s = str(m) if m else "—"
            print(f"{d:<{W[0]}} {g:>{W[1]}} {m_s:>{W[2]}} {a_s:>{W[3]}} {diff_s:>{W[4]}}")
        else:
            print(f"{d:<{W[0]}} {g:>{W[1]}} {a_s:>{W[2]}} {diff_s:>{W[3]}}")

    print(line)
    api_tot_s = str(api_tot) if not api_err else "ERR"
    if has_mp:
        print(f"{'ИТОГО':<{W[0]}} {gs_tot:>{W[1]}} {mp_tot:>{W[2]}} {api_tot_s:>{W[3]}}")
    else:
        print(f"{'ИТОГО':<{W[0]}} {gs_tot:>{W[1]}} {api_tot_s:>{W[2]}}")

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
    mp, mp_note = load_marketplace_csv()
    print(f"      {mp_note}")

    print(f"[3/3] API ЯМ ({args.days} дней)...")
    api, api_err = fetch_api(args.days)
    if api_err:
        print(f"      [ОШИБКА] {api_err}")
    else:
        print(f"      {sum(api.values())} записей после фильтра | {len(api)} дат")

    print_table(gs, mp, api, api_err, args.days, mp_note if mp is None else None)


if __name__ == "__main__":
    main()
