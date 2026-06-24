function Ozon_return_all() {
  try {
    const [apiKey, clientId] = get_setting();
    let full_data = [];
    
    // Начальные параметры для пагинации
    let last_id = 0; 
    let has_next = true;

    // Цикл для сбора всех страниц ответа
    while (has_next) { 
      let info_req = fetch_ozon_returns(500, last_id, apiKey, clientId);
      
      // Если данных нет, прерываем цикл
      if (!info_req.returns || info_req.returns.length === 0) break;

      full_data.push(...info_req.returns);
      
      has_next = info_req.has_next;
      // Получаем id последней записи для следующего запроса
      last_id = info_req.last_id || info_req.returns[info_req.returns.length - 1].id; 
    }

    logOzonDebugStats(full_data);
    if (full_data.length > 0) {
      writeDataToSheet(full_data, 'Выгрузка');
      appendLog(`[Ozon] Завершено — всего из API: ${full_data.length}`, '', '');
    } else {
      console.log('Нет новых возвратов за период.');
      appendLog('[Ozon] Нет новых возвратов за период', '', '');
    }
  } catch (error) {
    console.error('Произошла ошибка:', error);
    appendLog('[Ozon] Необработанная ошибка', '', String(error).substring(0, 300));
  }
}

// Переименовали функцию, так как теперь она тянет всё
function fetch_ozon_returns(limit, last_id, key, client_id) {   
  const date = getDateRange();
  
  const body = JSON.stringify({
    "filter": {
      "logistic_return_date": {
        "time_from": date.time_from,
        "time_to": date.time_to
      }
      // Удалили "visual_status_name": "ReceivedBySeller", чтобы получать и FBO возвраты
    },
    "limit": limit,
    "last_id": last_id
  });

  const options = {
    method: "POST",
    headers: {
      "Client-Id": String(client_id),
      "Api-Key": key
    },
    contentType: "application/json",
    payload: body
  };

  const response = UrlFetchApp.fetch("https://api-seller.ozon.ru/v1/returns/list", options);
  const responseCode = response.getResponseCode();
  const json = JSON.parse(response.getContentText());
  const recordCount = (json.returns || []).length;
  Logger.log(`[Ozon API] HTTP ${responseCode} | last_id: ${last_id} | записей в ответе: ${recordCount} | has_next: ${json.has_next}`);
  appendLog(`[Ozon] HTTP ${responseCode} last_id=${last_id} — ${recordCount} записей`, responseCode, responseCode !== 200 ? response.getContentText().substring(0, 300) : '');
  return json;
}

function writeDataToSheet(data, sheet_name) {
  const sheet = SpreadsheetApp.getActive().getSheetByName(sheet_name);

  // Получаем существующие ID из 2-й колонки (B: Номер отправления)
  let existingIds = [];
  const lastRow = sheet.getLastRow();
  
  if (lastRow > 1) {
    const existingData = sheet.getRange(2, 2, lastRow - 1, 1).getValues(); 
    existingIds = existingData.flat();
  }

  // Преобразуем дату в читаемый вид
  function formatDate(dateStr) {
    if (!dateStr) return "";
    const date = new Date(dateStr);
    return Utilities.formatDate(date, Session.getScriptTimeZone(), "yyyy-MM-dd HH:mm:ss");
  }

  const currentDate = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), "yyyy-MM-dd HH:mm:ss");

  // Формируем строки: строго 12 колонок (от A до L)
  const rows = data
    .filter(item => !existingIds.includes(item.posting_number))
    .map(item => {
      const schemaPrefix = item.schema ? `[${item.schema}] ` : "";
      const currentStatus = item.visual?.status_name || "Статус неизвестен";

      return [
        currentDate,                                    // Колонка A: Дата добавления
        item.posting_number,                            // Колонка B: Номер отправления
        item.logistic?.barcode || "",                   // Колонка C: Штрих-код возврата
        item.clearing_id || "",                         // Колонка D: ID отправления
        item.product?.offer_id || "",                   // Колонка E: Артикул
        schemaPrefix + currentStatus,                   // Колонка F: Статус (например: [FBS] Получен)
        item.return_reason_name || "",                  // Колонка G: Причина возврата
        formatDate(item.logistic?.return_date),         // Колонка H: Дата возврата
        item.schema === "ReceivedBySeller" ? formatDate(item.received_at) : "", // Колонка I: Дата выдачи (только ReceivedBySeller; ArrivedAtReturnPlace — ещё не выдан)
        item.product?.quantity || 0,                    // Колонка J: Количество
        item.product?.price?.price || 0,                // Колонка K: Цена
        item?.additional_info?.is_opened ? "Да" : "Нет" // Колонка L: Вскрытая упаковка
      ];
    });

  if (rows.length > 0) {
    // Начинаем запись со следующей пустой строки, но гарантированно не выше 2-й (чтобы не трогать заголовок)
    const startRow = Math.max(2, sheet.getLastRow() + 1);
    sheet.getRange(startRow, 1, rows.length, 12).setValues(rows);
    Logger.log(`Добавлено новых записей: ${rows.length}`);
  } else {
    Logger.log("Нет новых уникальных записей для добавления.");
  }
}

function get_setting(){
    var sheet = SpreadsheetApp.getActive().getSheetByName('Настройка');
    var KEY = sheet.getRange(2,1);
    KEY = KEY.getValue();

    var Client_id = sheet.getRange(2,2);
    Client_id = Client_id.getValue();
    console.log(KEY, Client_id)

    var sheet = SpreadsheetApp.getActive().getSheetByName('Выгрузка');

    return [KEY, Client_id]

}

function getDateRange() {
  // Получаем текущую дату и время
  const now = new Date();

  // Вычисляем дату и время за двое суток назад
  const twoDaysAgo = new Date(now.getTime() - 12 * 24 * 60 * 60 * 1000);

  // Форматируем даты в строку в формате ISO 8601 (с "Z" на конце)
  const timeTo = now.toISOString();
  const timeFrom = twoDaysAgo.toISOString();

  // Возвращаем объект с датами
  return {
    time_from: timeFrom,
    time_to: timeTo
  };
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
function logOzonDebugStats(data) {
  if (!data || data.length === 0) {
    Logger.log('[Ozon DEBUG] Нет данных для анализа.');
    return;
  }

  // Распределение по visual.status_name (с префиксом schema)
  const statusCounts = {};
  data.forEach(item => {
    const schema = item.schema ? `[${item.schema}] ` : '';
    const s = schema + (item.visual && item.visual.status_name ? item.visual.status_name : '(неизвестен)');
    statusCounts[s] = (statusCounts[s] || 0) + 1;
  });
  Logger.log(`[Ozon DEBUG] Всего записей из API: ${data.length}`);
  Logger.log('[Ozon DEBUG] Распределение по статусам:');
  Object.keys(statusCounts).sort().forEach(s => {
    Logger.log(`  ${s}: ${statusCounts[s]}`);
  });

  // received_at осмысленна только для ReceivedBySeller.
  // ArrivedAtReturnPlace — товар в ПВЗ, дата выдачи ещё не сформирована.
  const receivedData = data.filter(item => item.schema === "ReceivedBySeller");
  const arrivedData  = data.filter(item => item.schema === "ArrivedAtReturnPlace");
  Logger.log(`[Ozon DEBUG] ReceivedBySeller (есть received_at): ${receivedData.length}`);
  Logger.log(`[Ozon DEBUG] ArrivedAtReturnPlace (нет received_at, ждут выдачи): ${arrivedData.length}`);

  // Агрегация по received_at — только ReceivedBySeller
  const dateCounts = {};
  receivedData.forEach(item => {
    const d = (item.received_at || '').substring(0, 10);
    if (d >= '2020') dateCounts[d] = (dateCounts[d] || 0) + 1;
  });
  const dates = Object.keys(dateCounts).sort();
  Logger.log(`[Ozon DEBUG] Агрегация по received_at / ReceivedBySeller (${dates.length} дат):`);
  dates.forEach(d => Logger.log(`  ${d}: ${dateCounts[d]}`));

  // Вчерашний день отдельно
  const yesterday = new Date();
  yesterday.setDate(yesterday.getDate() - 1);
  const ydStr = Utilities.formatDate(yesterday, Session.getScriptTimeZone(), 'yyyy-MM-dd');
  Logger.log(`[Ozon DEBUG] Вчера (${ydStr}) ReceivedBySeller: ${dateCounts[ydStr] || 0}`);
}
