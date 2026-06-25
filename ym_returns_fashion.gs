// ================= НАСТРОЙКИ =================
const API_KEY = 'ACMA:fyrpztZMH8WM7z76istlJaxcTfi3jRbfXXOaAJnL:b7f4f021';       // Токен Яндекс Маркета (Обычно передается с приставкой Bearer или OAuth)
const CAMPAIGN_ID = '22209372'; // Идентификатор кампании (число)
const SHEET_NAME = 'Возвраты YM';      // Название листа для записи
const DAYS_TO_FETCH = 30;              // Период выгрузки (в днях)
// =============================================

// Настройка колонок и логика извлечения данных из вложенного JSON Яндекса
const COLUMNS_CONFIG = [
  { key: 'id', name: 'ID возврата/невыкупа', getValue: (r) => r.id },
  { key: 'orderId', name: 'Номер заказа', getValue: (r) => r.orderId },
  { key: 'returnType', name: 'Тип (Невыкуп/Возврат)', getValue: (r) => r.returnType },
  { key: 'shipmentStatus', name: 'Логистический статус', getValue: (r) => r.shipmentStatus },
  { key: 'refundStatus', name: 'Статус возврата денег', getValue: (r) => r.refundStatus || '' },
  { key: 'creationDate', name: 'Дата создания', getValue: (r) => r.creationDate },
  { key: 'updateDate', name: 'Дата обновления', getValue: (r) => r.updateDate },
  { key: 'pickupTillDate', name: 'Срок хранения (до)', getValue: (r) => r.pickupTillDate || '' },
  { key: 'amount', name: 'Сумма', getValue: (r) => r.amount ? r.amount.value : '' },
  { key: 'currency', name: 'Валюта', getValue: (r) => r.amount ? r.amount.currencyId : '' },
  { key: 'shipmentRecipientType', name: 'Способ возврата', getValue: (r) => r.shipmentRecipientType || '' },
  { key: 'logisticPoint', name: 'Название ПВЗ/Склада', getValue: (r) => r.logisticPickupPoint ? r.logisticPickupPoint.name : '' },
  // Собираем все товары в одну строку (Артикул: количество)
  { key: 'items', name: 'Товары (Ваш SKU : кол-во)', getValue: (r) => {
      if (!r.items || r.items.length === 0) return '';
      return r.items.map(i => `${i.shopSku} (${i.count} шт.)`).join(', ');
  }}
];

function fetchYmReturns() {
  const sheet = getOrCreateSheet(SHEET_NAME);
  let data = getYmData();
  logYmDebugStats(data);

  if (!data || data.length === 0) {
    Logger.log('Нет данных за выбранный период.');
    appendLog('[YM] Нет данных за период', '', '');
    return;
  }

  if (data && data.length > 0) {
      Logger.log('Пример первого объекта из API: ' + JSON.stringify(data[0], null, 2));
  }

  // --- ФИЛЬТРАЦИЯ ---
  // Оставляем только те возвраты/невыкупы, которые фактически выданы магазину (PICKED)
  data = data.filter(item => item.shipmentStatus === 'PICKED');

  if (data.length === 0) {
    Logger.log('За выбранный период нет возвратов со статусом "PICKED" (Выдано).');
    appendLog('[YM] Нет возвратов со статусом «PICKED»', '', '');
    return;
  }
  // ------------------

  // Считываем текущие данные из таблицы
  const existingRange = sheet.getDataRange();
  let existingValues = existingRange.getValues();

  // Добавляем заголовки, если таблица пустая
  if (existingValues.length <= 1 && existingValues[0][0] === "") {
    const headers = COLUMNS_CONFIG.map(col => col.name);
    sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
    sheet.getRange(1, 1, 1, headers.length).setFontWeight("bold");
    existingValues = [headers];
  }

  // existingValues[0] = заголовок (строка 1 в листе)
  // existingValues[i] = данные (строка i+1 в листе)
  const existingMap = {};
  for (let i = 1; i < existingValues.length; i++) {
    const returnId = existingValues[i][0];
    if (returnId) {
      existingMap[String(returnId)] = { sheetRow: i + 1, values: existingValues[i] };
    }
  }

  // updateDate меняется каждый раз — исключаем из сравнения, чтобы не было лишнего шума
  const SKIP_COMPARE = new Set(['updateDate']);

  const newRows = [];
  let updatedCount = 0;

  data.forEach(item => {
    const newRowValues = COLUMNS_CONFIG.map(col => {
      const val = col.getValue(item);
      return (val === null || val === undefined) ? "" : val;
    });
    const id = String(item.id);

    if (!existingMap.hasOwnProperty(id)) {
      // Новая запись — добавим в конец
      newRows.push(newRowValues);
    } else {
      // Существующая запись — сравниваем поля (кроме updateDate)
      const existing = existingMap[id];
      const changedFields = COLUMNS_CONFIG
        .map((col, idx) => {
          if (SKIP_COMPARE.has(col.key)) return null;
          const apiStr = String(newRowValues[idx]);
          const existStr = (existing.values[idx] === null || existing.values[idx] === undefined)
            ? "" : String(existing.values[idx]);
          return apiStr !== existStr ? `${col.name}: "${existStr}" → "${apiStr}"` : null;
        })
        .filter(Boolean);

      if (changedFields.length > 0) {
        // Перезаписываем строку и подсвечиваем жёлтым
        const rowRange = sheet.getRange(existing.sheetRow, 1, 1, COLUMNS_CONFIG.length);
        rowRange.setValues([newRowValues]);
        rowRange.setBackground('#fff2cc');
        updatedCount++;
        const logMsg = `[YM] Обновлена запись ID=${item.id}: ${changedFields.join(' | ')}`;
        Logger.log(logMsg);
        appendLog(logMsg, '', '');
      }
    }
  });

  // Дописываем новые строки в конец таблицы
  if (newRows.length > 0) {
    const lastRow = sheet.getLastRow();
    const newRange = sheet.getRange(lastRow + 1, 1, newRows.length, COLUMNS_CONFIG.length);
    newRange.setValues(newRows);
    newRange.setBackground('#efefef'); // серый фон для новых строк
  }

  if (newRows.length === 0 && updatedCount === 0) {
    Logger.log('Нет ни новых, ни изменившихся записей.');
    appendLog('[YM] Нет изменений', '', '');
    return;
  }

  Logger.log(`Добавлено новых: ${newRows.length}. Обновлено изменившихся: ${updatedCount}.`);
  appendLog(`[YM] Добавлено новых: ${newRows.length}, обновлено: ${updatedCount}`, '', '');
}

// Вспомогательная функция для запроса данных из Яндекс Маркета (с пагинацией)
function getYmData() {
  const timezone = Session.getScriptTimeZone();
  const today = new Date();

  const pastDate = new Date();
  pastDate.setDate(today.getDate() - DAYS_TO_FETCH);

  const toDate = Utilities.formatDate(today, timezone, 'yyyy-MM-dd');
  const fromDate = Utilities.formatDate(pastDate, timezone, 'yyyy-MM-dd');

  let allReturns = [];
  let pageToken = "";

  // Цикл для пролистывания страниц API
  do {
    let url = `https://api.partner.market.yandex.ru/v2/campaigns/${CAMPAIGN_ID}/returns?fromDate=${fromDate}&toDate=${toDate}&limit=100`;
    if (pageToken) {
      url += `&pageToken=${pageToken}`;
    }

    // В зависимости от типа вашего токена, Яндексу иногда нужен Bearer, а иногда Api-Key.
    // Если используете Api-Key, то заголовок может выглядеть так: 'Api-Key': API_KEY
    const options = {
      method: 'get',
      headers: {
        'Api-Key': API_KEY
      },
      muteHttpExceptions: true
    };

    const response = UrlFetchApp.fetch(url, options);
    const responseCode = response.getResponseCode();
    Logger.log(`[YM API] HTTP ${responseCode}${pageToken ? ' [стр.+]' : ' [стр.1]'} | накоплено: ${allReturns.length}`);

    if (responseCode !== 200) {
      const errText = response.getContentText().substring(0, 300);
      Logger.log(`[YM API] Ошибка: ${errText}`);
      appendLog('[YM] API ошибка', responseCode, errText);
      break;
    }

    const json = JSON.parse(response.getContentText());
    const pageReturns = (json.result && json.result.returns) ? json.result.returns : [];
    allReturns = allReturns.concat(pageReturns);
    Logger.log(`[YM API] Записей на странице: ${pageReturns.length} | итого: ${allReturns.length}`);
    appendLog(`[YM] API${pageToken ? ' стр.+' : ' стр.1'} — ${pageReturns.length} записей, итого: ${allReturns.length}`, responseCode, '');

    // Проверяем, есть ли следующая страница
    if (json.result && json.result.paging && json.result.paging.nextPageToken) {
      pageToken = json.result.paging.nextPageToken;
    } else {
      pageToken = ""; // Конец цикла
    }

  } while (pageToken);

  Logger.log(`[YM API] Итого получено записей: ${allReturns.length}`);
  return allReturns;
}

function getOrCreateSheet(sheetName) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(sheetName);

  if (!sheet) {
    sheet = ss.insertSheet(sheetName);
  }
  return sheet;
}

// Создаем кнопку в интерфейсе
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('📦 YM Аналитика')
    .addItem('🔄 Обновить возвраты (Выдано)', 'fetchYmReturns')
    .addToUi();
}


// ===== Лог в лист «Лог» — вставка после строки 1 (Z→A: новые записи сверху) =====
function appendLog(message, responseCode, errorMessage) {
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    let sheet = ss.getSheetByName('Лог');
    if (!sheet) {
      sheet = ss.insertSheet('Лог');
      sheet.getRange(1, 1, 1, 4).setValues([['Дата', 'Сообщение', 'Код ответа', 'Ошибка']]);
      sheet.getRange(1, 1, 1, 4).setFontWeight('bold');
    }
    const now = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'yyyy-MM-dd HH:mm:ss');
    sheet.insertRowAfter(1);
    sheet.getRange(2, 1, 1, 4).setValues([[now, message, responseCode !== '' ? responseCode : '', errorMessage || '']]);
  } catch (e) {
    Logger.log('[appendLog error] ' + e);
  }
}

// ===== DEBUG: логирование статусов и агрегация по датам =====
function logYmDebugStats(data) {
  if (!data || data.length === 0) {
    Logger.log('[YM DEBUG] Нет данных для анализа.');
    return;
  }

  // Распределение по shipmentStatus до фильтра
  const statusCounts = {};
  data.forEach(item => {
    const s = item.shipmentStatus || '(пусто)';
    statusCounts[s] = (statusCounts[s] || 0) + 1;
  });
  Logger.log(`[YM DEBUG] Всего записей из API: ${data.length}`);
  Logger.log('[YM DEBUG] Распределение по shipmentStatus:');
  Object.keys(statusCounts).sort().forEach(s => {
    Logger.log(`  ${s}: ${statusCounts[s]}`);
  });

  // Агрегация по датам для статуса PICKED
  const filtered = data.filter(item => item.shipmentStatus === 'PICKED');
  Logger.log(`[YM DEBUG] Записей «PICKED»: ${filtered.length}`);
  const dateCounts = {};
  filtered.forEach(item => {
    const d = (item.creationDate || '').substring(0, 10);
    if (d >= '2020') dateCounts[d] = (dateCounts[d] || 0) + 1;
  });
  const dates = Object.keys(dateCounts).sort();
  Logger.log(`[YM DEBUG] Агрегация «PICKED» по датам (${dates.length} дат):`);
  dates.forEach(d => Logger.log(`  ${d}: ${dateCounts[d]}`));

  // Вчерашний день отдельно
  const yesterday = new Date();
  yesterday.setDate(yesterday.getDate() - 1);
  const ydStr = Utilities.formatDate(yesterday, Session.getScriptTimeZone(), 'yyyy-MM-dd');
  Logger.log(`[YM DEBUG] Вчера (${ydStr}) «PICKED»: ${dateCounts[ydStr] || 0}`);
}