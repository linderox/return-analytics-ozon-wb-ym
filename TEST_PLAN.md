# Returns Data Verification — Test Plan
**Date:** 2026-06-23
**Scope:** Ozon · WildBerries · Yandex Market
**Goal:** Confirm that Google Sheets reflects current marketplace API data; identify and fix data gaps.

---

## System Overview

```
Marketplace API
      │
      │  HTTP (scheduled trigger, every N hours)
      ▼
Google Apps Script (.gs)
      │  filter → deduplicate → append
      ▼
Google Sheets tab ("Возвраты WB", "Возвраты YM", etc.)
      │  manual CSV export
      ▼
CSV snapshot in returns/           ← Python scripts compare against this
      │
      ▼
XLSX from marketplace cabinet      ← ground-truth / historical reference
```

Each Python script mirrors the GS logic so it can be run locally to diagnose
why the GS isn't writing data.

---

## Snapshot — Current GS CSV State (as of 2026-06-23)

| Marketplace | CSV file                       | Rows (excl. header) | Last date in CSV | Gap (days) |
|-------------|--------------------------------|---------------------|------------------|------------|
| Ozon        | ozon_returns_gs.csv            | 2 417               | 2026-06-23       | 0 ✅        |
| WB          | wb-returns-google-sheet.csv    | 119                 | 2026-06-18       | **5** ⚠️   |
| YM          | ym_returns_google_sheet.csv    | 53                  | 2026-06-15       | **8** ❌    |

---

## TC-1 — WildBerries Returns

**Script:** `python returns/wb_returns.py`
**GS script:** `wb_returns_fashion.gs` → sheet "Возвраты WB"
**Shop:** oid=158816 (fashion)
**Unique key:** `srid`
**GS filter:** `status == "Выдано"`
**API endpoint:** `GET /api/v1/analytics/goods-return?dateFrom=…&dateTo=…`

### Steps

| # | Action | Expected result |
|---|--------|-----------------|
| 1 | Run `python returns/wb_returns.py` | Script prints token info, CSV state, API result |
| 2 | Check token section | `Days remaining > 0` (expires 2026-10-04, 103 days) |
| 3 | Check CSV snapshot | 119 rows, last date 2026-06-18 |
| 4 | Check API response | HTTP 200 with ≥ 76 records (or 429 — see Known Issues) |
| 5 | Check status breakdown | `"Выдано"` is the dominant status |
| 6 | Check overlap section | ≥ 26 new srids not in CSV (gap since 2026-06-18) |
| 7 | Compare XLSX vs GS CSV | `wb_returns_report_marketplace.csv` → 565 rows; GS has 119 — backfill needed |

### Pass criteria
- Token valid (not expired)
- HTTP 200 from API (may need retry after 429)
- At least 1 new srid in the last 5 days not in CSV
- Status `"Выдано"` still exists in API response

### Fail / action required

| Symptom | Root cause | Fix |
|---------|-----------|-----|
| HTTP 429 | WB analytics rate limit | Wait 60 s, retry; fix GS script (see below) |
| HTTP 401 | Token revoked | Generate new token in WB cabinet |
| HTTP 403 | Wrong token scope | Regenerate with "Аналитика" scope (acc=1) |
| 0 records | No returns for oid=158816 in 30 d | Extend to 60 d window |
| 0 `"Выдано"` | Status string changed | Check ALL STATUSES output, update GS filter |
| 0 new srids + CSV date old | Dedup logic blocking all writes | Wipe sheet and re-run to backfill |

### Known issue — GS does not handle 429
`getWbData()` in `wb_returns_fashion.gs` returns `[]` on any non-200 response,
including 429. The fix:

```javascript
// In getWbData(), replace the error return block:
if (responseCode === 429) {
  Logger.log('Rate limit 429 — waiting 60 s...');
  Utilities.sleep(60000);
  // retry once
  const retry = UrlFetchApp.fetch(url, options);
  if (retry.getResponseCode() !== 200) {
    Logger.log('Still 429 after retry. Aborting.');
    return [];
  }
  return parseWbResponse(retry.getContentText());
}
```

### XLSX discrepancy
- `wb_returns_report_marketplace.xlsx`: **565 data rows** (downloaded directly from WB cabinet)
- GS CSV: **119 rows**
- The XLSX covers a longer historical window. After fixing the trigger, consider a
  one-time backfill by importing the XLSX data manually into the GSheet.

---

## TC-2 — Yandex Market Returns

**Script:** `python returns/ym_returns.py`
**GS script:** `ym_returns_fashion.gs` → sheet "Возвраты YM"
**Shop:** campaign_id=22209372
**Unique key:** return `id` (integer)
**GS filter:** `shipmentStatus == "PICKED"`
**API endpoint:** `GET /v2/campaigns/{id}/returns?fromDate=…&toDate=…&limit=100`

### Steps

| # | Action | Expected result |
|---|--------|-----------------|
| 1 | Run `python returns/ym_returns.py` | Script prints credentials, CSV state, API result |
| 2 | Check CSV snapshot | 53 rows, last date 2026-06-15 |
| 3 | Check API response | HTTP 200 with ≥ 57 records (30-day window) |
| 4 | Check shipmentStatus breakdown | `"PICKED"` appears (46 in last confirmed run) |
| 5 | Check overlap section | ≥ 11 new IDs not in CSV (gap since 2026-06-15) |
| 6 | Check XLSX vs GS | XLSX (`ym_united_returns_...`) is report-style (18 rows) — not comparable row-for-row |

### Pass criteria
- HTTP 200 from API
- At least 1 new return ID since 2026-06-15 not in CSV
- `"PICKED"` status still present in API

### Fail / action required

| Symptom | Root cause | Fix |
|---------|-----------|-----|
| HTTP 401 | API key revoked | Generate new key in YM Partner cabinet |
| HTTP 403 | Wrong campaign or key scope | Verify CAMPAIGN_ID=22209372 matches the fashion shop |
| HTTP 404 | Campaign not found | Check campaign ID in YM cabinet |
| 0 records | No returns in 30 d | Try 90-day window (script does this automatically) |
| 0 `"PICKED"` | Status renamed | Check ALL STATUSES output, update `fetchYmReturns()` filter |
| New IDs found but not in GS | **Trigger stopped** | See fix below ← root cause confirmed |

### Known issue — GS trigger stopped (root cause confirmed)
Data exists in API (57 records, 46 PICKED) but has not been written since 2026-06-15.
The GS script `fetchYmReturns()` is not being called on schedule.

**Fix:**
1. Open the GSheet → Extensions → Apps Script
2. Click the clock icon (Triggers) in the left sidebar
3. Check if a trigger exists for `fetchYmReturns` — if not, click "+ Add Trigger"
4. Settings: function=`fetchYmReturns`, event source=`Time-driven`, type=`Hours timer`, interval=`Every 6 hours`
5. Save → verify it fires within 6 hours by checking the "Execution log"

---

## TC-3 — Ozon Returns

**Script:** `python returns/ozon_returns.py --client-id <id> --api-key <key>`
**GS script:** `ozon_returns_fashion.gs` → (fashion shop GSheet)
**Unique key:** `posting_number`
**GS filter:** `logistic_return_date` window (12-day default in .gs)
**API endpoint:** `POST /v1/returns/list`

### Steps

| # | Action | Expected result |
|---|--------|-----------------|
| 1 | Open the fashion GSheet → "Настройка" tab | Find `seller_client_id` and `seller_api_key` |
| 2 | Run script with those credentials | `python returns/ozon_returns.py --client-id <id> --api-key <key>` |
| 3 | Check available shops list | Confirms which client_id maps to which prefix |
| 4 | Check CSV snapshot | 2 417 rows, last date 2026-06-23 (Ozon is up to date) |
| 5 | Check API response | HTTP 200; record count depends on fashion shop's activity |
| 6 | Check overlap section | Should show minimal new posting_numbers if GS is current |
| 7 | Check `visual.status_name` | Will appear as `null` in API → GS shows "Статус неизвестен" (expected) |

### Pass criteria
- HTTP 200 from API with fashion shop credentials
- New posting_numbers ≈ 0 (GS CSV is current as of 2026-06-23)
- `visual.status_name = null` confirmed as acceptable (not a bug)

### Fail / action required

| Symptom | Root cause | Fix |
|---------|-----------|-----|
| HTTP 401/403 | Wrong `seller_client_id` or `seller_api_key` | Re-read from "Настройка" tab |
| 0 records in 12-day window | No returns yet | Try 60-day window (`fetch_ozon_returns(…, 60)`) |
| Many new posting_numbers | GS trigger stopped or wrong shop tested | Verify client_id matches fashion shop |
| `visual.status_name = null` | Ozon API omits this field for some returns | Not a bug; handled by GS fallback |

### Note on shop_id1 (uf prefix)
Running the script with `--shop shop_id1` tests a **different** shop (home textiles, prefix=uf).
That shop's posting_numbers have 0 overlap with `ozon_returns_gs.csv` because the CSV
belongs to the fashion shop. Always use `--client-id`/`--api-key` from the GSheet
"Настройка" tab when testing the fashion shop.

---

## TC-4 — XLSX vs GS CSV Cross-check

For each marketplace, the XLSX downloaded directly from the cabinet is the authoritative
historical record. Compare it against the GS CSV to measure the true backfill gap.

| File | XLSX rows | GS CSV rows | Gap | Action |
|------|-----------|-------------|-----|--------|
| `wb_returns_report_marketplace` | 565 | 119 | **446 rows** | One-time backfill |
| `ozon_returns__report_marketplace_*` | summary (6 rows) | 2 417 | N/A — XLSX is not raw data |
| `ym_united_returns_*` | report-style (18 rows) | 53 | N/A — different format |

**WB backfill procedure (manual):**
1. Open `wb_returns_report_marketplace.xlsx` in Excel / Sheets
2. Filter rows where "Статус возврата" == "Выдано"
3. Map columns to GS column order (COLUMNS_CONFIG in `wb_returns_fashion.gs`)
4. Paste into the GSheet below existing rows; deduplication by srid will prevent doubles
   if `fetchWbReturns()` runs after the paste (it only updates, not duplicates)

---

## Run Order

```bash
# 1. Run all three checks (requires packages: requests, xlsx2csv in venv)
cd d:/python/ozon-api-nikita-victoria

# WB (may get 429 — run once, wait 60 s if needed, run again)
python returns/wb_returns.py

# YM
python returns/ym_returns.py

# Ozon — replace placeholders with values from GSheet "Настройка" tab
python returns/ozon_returns.py --client-id <FASHION_CLIENT_ID> --api-key <FASHION_API_KEY>
```

---

## Summary of Required Actions

| Priority | Marketplace | Action | Who |
|----------|------------|--------|-----|
| HIGH | YM | Re-create Apps Script trigger for `fetchYmReturns()` | GSheet admin |
| HIGH | WB | Add 429 retry in `getWbData()` in `wb_returns_fashion.gs` | GSheet admin |
| MEDIUM | Ozon | Confirm fashion shop credentials from "Настройка" tab; run TC-3 | Developer |
| MEDIUM | WB | One-time backfill of 446 missing rows from XLSX | GSheet admin |
| LOW | WB | Verify trigger fires after 429 fix is deployed | Developer |
| LOW | All | Re-run Python scripts after fixes to confirm 0 new records | Developer |
