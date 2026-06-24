#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
returns/ozon_dates.py

Сравнение количества возвратов по датам из трёх источников:
  1. GS CSV          — ozon_returns_gs.csv
  2. Маркетплейс CSV — ozon_returns__report_marketplace_*.csv (из XLSX кабинета Ozon)
  3. API Ozon        — /v1/returns/list (12 дней, как в GS-скрипте)

Фильтра по статусу нет (как в ozon_returns_fashion.gs — все возвраты).
Дата группировки: logistic.return_date → колонка H "Дата возврата" в GS CSV.

Usage:
    python returns/ozon_dates.py [--shop shop_id1]
    python returns/ozon_dates.py --client-id 465010 --api-key d704b9fb-...
    python returns/ozon_dates.py --days 60
"""

import argparse
import csv
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone

import requests

RETURNS_DIR = os.path.dirname(os.path.abspath(__file__))

OZON_URL = "https://api-seller.ozon.ru/v1/returns/list"
CLIENT_SECRET_OZON = "1d3af06e-b862-4830-8ade-7880fa1ca8ae"
CLIENT_ID_OZON = "141168"

def read_csv(path):
    if not os.path.exists(path):
        return [], []
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    return (rows[0] if rows else []), (rows[1:] if len(rows) > 1 else [])


def load_gs_csv():
    """
    GS CSV: col 7 = "Дата возврата" (logistic.return_date, формат "YYYY-MM-DD HH:MM:SS").
    Данные без фильтра по статусу — GS-скрипт пишет все возвраты за 12-дневное окно.
    """
    path = os.path.join(RETURNS_DIR, "ozon_returns_gs.csv")
    _, rows = read_csv(path)
    counts = defaultdict(int)
    for r in rows:
        d = r[7][:10] if len(r) > 7 and r[7] else ""
        if d >= "2020":
            counts[d] += 1
    return counts, len(rows), path


def _parse_ozon_mp_date(raw: str) -> str:
    """Ozon XLSX экспортирует даты в формате MM/DD/YY HH:MM → YYYY-MM-DD."""
    raw = raw.strip()
    for fmt in ("%m/%d/%y %H:%M", "%m/%d/%y"):
        try:
            return datetime.strptime(raw[:len(fmt.replace("%m","00").replace("%d","00").replace("%y","00").replace("%H","00").replace("%M","00"))], fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    # попытка YYYY-MM-DD напрямую
    if len(raw) >= 10 and raw[4] == "-":
        return raw[:10]
    return ""


def _parse_date_mmddyy(raw: str) -> str:
    raw = raw.strip()
    if not raw:
        return ""
    if len(raw) >= 10 and raw[4] == "-":
        return raw[:10]
    for fmt in ("%m/%d/%y %H:%M", "%m/%d/%y %H:%M:%S", "%m/%d/%y"):
        try:
            return datetime.strptime(raw[:16], fmt[:len(fmt)]).strftime("%Y-%m-%d")
        except Exception:
            pass
    return ""


def load_marketplace_csv():
    """
    Маркетплейс CSV (конвертирован из XLSX кабинета Ozon).
    Первые пустые строки пропускаем.
    col 2  = posting_number
    col 6  = дата возврата (MM/DD/YY HH:MM)
    """
    import glob
    pattern = os.path.join(RETURNS_DIR, "ozon_returns__report_marketplace_*.csv")
    files = sorted(glob.glob(pattern))
    if not files:
        return None, 0, "файл не найден"

    path = files[-1]
    _, rows = read_csv(path)

    # Пропускаем пустые/служебные строки в начале
    data_rows = [r for r in rows if any(cell.strip() for cell in r)]

    counts = defaultdict(int)
    for r in data_rows:
        raw_date = r[6] if len(r) > 6 else ""
        d = _parse_date_mmddyy(raw_date)
        if d >= "2020":
            counts[d] += 1

    total = sum(counts.values())
    note = f"{len(data_rows)} строк | {os.path.basename(path)}"
    return counts, total, note


def fetch_api(client_id, api_key, days):
    now = datetime.now(tz=timezone.utc)
    time_from = (now - timedelta(days=days)).isoformat()
    time_to = now.isoformat()

    all_returns = []
    last_id = 0
    has_next = True

    while has_next:
        body = {
            "filter": {"logistic_return_date": {"time_from": time_from, "time_to": time_to}},
            "limit": 500,
            "last_id": last_id,
        }
        try:
            resp = requests.post(
                OZON_URL,
                json=body,
                headers={"Client-Id": str(client_id), "Api-Key": api_key},
                timeout=30,
            )
        except Exception as e:
            return None, f"Ошибка соединения: {e}"

        if resp.status_code != 200:
            return None, f"HTTP {resp.status_code}: {resp.text[:300]}"

        data = resp.json()
        returns = data.get("returns") or []
        if not returns:
            break
        all_returns.extend(returns)
        has_next = bool(data.get("has_next"))
        last_id = data.get("last_id") or (returns[-1].get("id", 0) if returns else 0)

    # received_at имеет смысл только для ReceivedBySeller.
    # ArrivedAtReturnPlace — товар в ПВЗ, дата выдачи ещё не сформирована.
    received = [r for r in all_returns if r.get("schema") == "ReceivedBySeller"]
    arrived_count = sum(1 for r in all_returns if r.get("schema") == "ArrivedAtReturnPlace")

    counts = defaultdict(int)
    for r in received:
        d = (r.get("received_at") or "")[:10]
        if d >= "2020":
            counts[d] += 1

    if all_returns:
        sample = received[0] if received else all_returns[0]
        sample_label = "ReceivedBySeller" if received else all_returns[0].get("schema", "first")
        print(f"\n  [JSON — {sample_label}]")
        print("  " + json.dumps(sample, ensure_ascii=False, indent=2).replace("\n", "\n  "))

    return counts, arrived_count, None


def print_table(gs, mp, api, api_err, days, mp_note, arrived_count=0):
    all_dates = sorted(set(gs) | (set(mp) if mp else set()) | (set(api) if api else set()))

    has_mp = bool(mp)
    W = [12, 10, 14, 12, 16] if has_mp else [12, 10, 12, 16]
    line = "─" * (sum(W) + len(W) - 1)

    print()
    print(f"Ozon — количество возвратов по датам  (только ReceivedBySeller, дата = received_at)")
    if arrived_count:
        print(f"  ArrivedAtReturnPlace (в ПВЗ, ждут выдачи, нет received_at): {arrived_count}")
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
            m_s = str(m) if m is not None else "—"
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
    parser.add_argument("--client-id")
    parser.add_argument("--api-key")
    parser.add_argument("--days", type=int, default=12, help="Окно запроса (дней, по умолчанию 12 как в GS-скрипте)")
    args = parser.parse_args()

    if args.client_id and args.api_key:
        client_id, api_key = args.client_id, args.api_key
        label = f"client_id={client_id} (ручной ввод)"
    else:
        client_id, api_key = CLIENT_ID_OZON, CLIENT_SECRET_OZON
        label = f"CLIENT_ID_OZON={client_id}"

    print(f"Магазин: {label}")
    print()

    print("[1/3] GS CSV...")
    gs, gs_total, gs_path = load_gs_csv()
    print(f"      {gs_total} строк | {len(gs)} дат | {os.path.basename(gs_path)}")

    print("[2/3] Маркетплейс CSV...")
    mp, mp_total, mp_note = load_marketplace_csv()
    if mp is None:
        print(f"      {mp_note}")
    else:
        print(f"      {mp_total} строк | {mp_note}")

    print(f"[3/3] API Ozon ({args.days} дней)...")
    api, arrived_count, api_err = fetch_api(client_id, api_key, args.days)
    if api_err:
        print(f"      [ОШИБКА] {api_err}")
    else:
        print(f"      ReceivedBySeller: {sum(api.values())} записей | {len(api)} дат")
        print(f"      ArrivedAtReturnPlace (нет received_at): {arrived_count}")

    print_table(gs, mp, api, api_err, args.days, mp_note if mp is None else None, arrived_count)


if __name__ == "__main__":
    main()
