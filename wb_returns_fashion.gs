// ================= НАСТРОЙКИ =================
const API_KEY = 'eyJhbGciOiJFUzI1NiIsImtpZCI6IjIwMjYwMzAydjEiLCJ0eXAiOiJKV1QifQ.eyJhY2MiOjMsImVudCI6MSwiZXhwIjoxNzk4MDIwOTEyLCJmb3IiOiJzZWxmIiwiaWQiOiIwMTllZjY4ZC0zZGM5LTczMGMtYjU4MS00MTdmYjg4YzY5MTAiLCJpaWQiOjI2Njk5MDU3LCJvaWQiOjE1ODgxNiwicyI6MTA3Mzc0MzkwOCwic2lkIjoiNTgwMjQ2OGYtZDQ3NS00M2ZmLTgxMjAtYzFlMTY2MTdkMmI3IiwidCI6ZmFsc2UsInVpZCI6MjY2OTkwNTd9.FjhUt0FV9yIzI-YYkCTVT_5iijp_FE6g0FcaNkH8bkr4gYzVC78Gl2nCTtOu2GjWGgX6M7aHsyLTAXjgIhmeuA'
const DAYS_TO_FETCH = 30; // Период загрузки (максимум 31 день по правилам API)
// =============================================

// Конфигурация заголовков и их локализация (порядок столбцов в таблице)
const COLUMNS_CONFIG = [
  { key: 'srid', name: 'Уникальный ID заказа на возврат (srid)' },
  { key: 'orderDt', name: 'Дата заказа на возврат' },
  { key: 'nmId', name: 'Артикул WB' },
  { key: 'brand', name: 'Бренд' },
  { key: 'subjectName', name: 'Предмет' },
  { key: 'techSize', name: 'Размер' },
  { key: 'barcode', name: 'Баркод' },
  { key: 'shkId', name: 'Штрихкод' },
  { key: 'returnType', name: 'Тип возврата' },
  { key: 'reason', name: 'Причина возврата' },
  { key: 'status', name: 'Статус возврата' },
  { key: 'isStatusActive', name: 'Тип статуса (0-архив, 1-актив)' },
  { key: 'readyToReturnDt', name: 'Дата и время готовности' },
  { key: 'completedDt', name: 'Дата и время выдачи' },
  { key: 'expiredDt', name: 'Дата и время истечения срока' },
  { key: 'dstOfficeId', name: 'ID ПВЗ выдачи' },
  { key: 'dstOfficeAddress', name: 'Адрес ПВЗ выдачи' },
  { key: 'orderId', name: 'Номер сборочного задания' },
  { key: 'stickerId', name: 'Стикер заказа на возврат' }
];

function fetchWbReturns() {
  const sheet = getOrCreateSheet(SHEET_NAME);
  let data = getWbData(); // Получаем данные из API
  logWbDebugStats(data);

  if (!data || data.length === 0) {
    Logger.log('Нет данных за выбранный период.');
    appendLog('[WB] Нет данных за период', '', '');
    return;
  }

  // --- ФИЛЬТРАЦИЯ ---
  // Оставляем только те записи, где статус в точности равен "Выдано"
  data = data.filter(item => item.status === 'Выдано');

  if (data.length === 0) {
    Logger.log('За выбранный период нет возвратов со статусом "Выдано".');
    appendLog('[WB] Нет возвратов со статусом «Выдано»', '', '');
    return;
  }
  // ------------------

  // Считываем текущие данные из таблицы для предотвращения дубликатов
  const existingRange = sheet.getDataRange();
  let existingValues = existingRange.getValues();
  
  // Если таблица пустая, добавляем заголовки
  if (existingValues.length <= 1 && existingValues[0][0] === "") {
    const headers = COLUMNS_CONFIG.map(col => col.name);
    sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
    sheet.getRange(1, 1, 1, headers.length).setFontWeight("bold");
    existingValues = [headers];
  }

  // Создаем карту существующих записей по srid
  const existingMap = {};
  for (let i = 1; i < existingValues.length; i++) {
    const srid = existingValues[i][0];
    if (srid) {
      existingMap[srid] = i;
    }
  }

  let updatedCount = 0;
  let addedCount = 0;

  // Обрабатываем отфильтрованные данные
  data.forEach(item => {
    const rowValues = COLUMNS_CONFIG.map(col => {
      let val = item[col.key];
      return (val === null || val === undefined) ? "" : val;
    });

    const srid = item.srid;

    if (existingMap.hasOwnProperty(srid)) {
      const rowIndex = existingMap[srid];
      existingValues[rowIndex] = rowValues;
      updatedCount++;
    } else {
      existingValues.push(rowValues);
      existingMap[srid] = existingValues.length - 1;
      addedCount++;
    }
  });

  // Записываем результат обратно в таблицу
  sheet.clearContents();
  sheet.getRange(1, 1, existingValues.length, COLUMNS_CONFIG.length).setValues(existingValues);
  
  Logger.log(`Фильтр применен. Добавлено "Выдано": ${addedCount}. Обновлено: ${updatedCount}.`);
  appendLog(`[WB] Завершено — добавлено: ${addedCount}, обновлено: ${updatedCount}`, '', '');
}

// Вспомогательная функция для запроса к API
function getWbData() {
  const timezone = Session.getScriptTimeZone();
  const today = new Date();
  
  const pastDate = new Date();
  pastDate.setDate(today.getDate() - DAYS_TO_FETCH);
  
  const dateTo = Utilities.formatDate(today, timezone, 'yyyy-MM-dd');
  const dateFrom = Utilities.formatDate(pastDate, timezone, 'yyyy-MM-dd');

  const url = `https://seller-analytics-api.wildberries.ru/api/v1/analytics/goods-return?dateFrom=${dateFrom}&dateTo=${dateTo}`;
  
  const options = {
    method: 'get',
    headers: {
      'Authorization': API_KEY
    },
    muteHttpExceptions: true
  };

  const response = UrlFetchApp.fetch(url, options);
  const responseCode = response.getResponseCode();
  
  Logger.log(`[WB API] HTTP ${responseCode} | URL: ${url}`);
  if (responseCode !== 200) {
    const errText = response.getContentText().substring(0, 300);
    Logger.log(`[WB API] Ошибка: ${errText}`);
    appendLog('[WB] API ошибка', responseCode, errText);
    return [];
  }

  const json = JSON.parse(response.getContentText());
  const records = Array.isArray(json) ? json : (json && Array.isArray(json.report) ? json.report : []);
  Logger.log(`[WB API] Получено записей: ${records.length}`);
  appendLog(`[WB] API запрос — ${records.length} записей`, responseCode, '');
  return records;
}

// Вспомогательная функция для получения или создания листа
function getOrCreateSheet(sheetName) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(sheetName);
  
  if (!sheet) {
    sheet = ss.insertSheet(sheetName);
  }
  return sheet;
}


// Функция для создания меню в интерфейсе Google Таблиц
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('📦 WB Аналитика') // Название меню на панели
    .addItem('🔄 Обновить возвраты (Выдано)', 'fetchWbReturns') // Название кнопки и функция, которую она запускает
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
function logWbDebugStats(data) {
  if (!data || data.length === 0) {
    Logger.log('[WB DEBUG] Нет данных для анализа.');
    return;
  }

  // Распределение по статусам до фильтра
  const statusCounts = {};
  data.forEach(item => {
    const s = item.status || '(пусто)';
    statusCounts[s] = (statusCounts[s] || 0) + 1;
  });
  Logger.log(`[WB DEBUG] Всего записей из API: ${data.length}`);
  Logger.log('[WB DEBUG] Распределение по статусам:');
  Object.keys(statusCounts).sort().forEach(s => {
    Logger.log(`  ${s}: ${statusCounts[s]}`);
  });

  // Агрегация по датам для статуса «Выдано»
  const filtered = data.filter(item => item.status === 'Выдано');
  Logger.log(`[WB DEBUG] Записей «Выдано»: ${filtered.length}`);
  const dateCounts = {};
  filtered.forEach(item => {
    const d = (item.orderDt || '').substring(0, 10);
    if (d >= '2020') dateCounts[d] = (dateCounts[d] || 0) + 1;
  });
  const dates = Object.keys(dateCounts).sort();
  Logger.log(`[WB DEBUG] Агрегация «Выдано» по датам (${dates.length} дат):`);
  dates.forEach(d => Logger.log(`  ${d}: ${dateCounts[d]}`));

  // Вчерашний день отдельно
  const yesterday = new Date();
  yesterday.setDate(yesterday.getDate() - 1);
  const ydStr = Utilities.formatDate(yesterday, Session.getScriptTimeZone(), 'yyyy-MM-dd');
  Logger.log(`[WB DEBUG] Вчера (${ydStr}) «Выдано»: ${dateCounts[ydStr] || 0}`);
}