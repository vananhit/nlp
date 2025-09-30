/**
 * @OnlyCurrentDoc
 */

// --- CONFIGURATION ---
const BACKEND_URL = 'https://control0001.com'; // <--- THAY THẾ BẰNG URL THỰC TẾ
const INPUT_SHEET_NAME = 'Input';
const OUTPUT_SHEET_NAME = 'Output';

// --- CONSTANTS FOR COLUMN INDEXES (1-based) ---
const ID_COL = 1;
const CONTENT_COL = 2;
const TOPIC_COL = 3;
const INTENT_COL = 4;
const STATUS_COL = 5;

// --- UI FUNCTIONS ---

/**
 * Creates a custom menu in the spreadsheet UI.
 */
function onOpen() {
  SpreadsheetApp.getUi()
      .createMenu('Công cụ SEO')
      .addItem('1. Tạo Template làm việc', 'createTemplate')
      .addItem('2. Thêm dòng mới', 'addNewRow')
      .addSeparator()
      .addItem('3. Phân tích Nội dung (Dòng chờ duyệt đầu tiên)', 'processFirstPendingRow')
      .addSeparator()
      .addItem('4. Cấu hình', 'showConfigurationSidebar')
      .addToUi();
}

/**
 * Shows the configuration sidebar.
 */
function showConfigurationSidebar() {
  const html = HtmlService.createHtmlOutputFromFile('Sidebar')
      .setTitle('Cấu hình Kết nối')
      .setWidth(300);
  SpreadsheetApp.getUi().showSidebar(html);
}

/**
 * Creates the 'Input' and 'Output' sheets with a more robust structure and formatting.
 */
function createTemplate() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const ui = SpreadsheetApp.getUi();

  if (ss.getSheetByName(INPUT_SHEET_NAME) || ss.getSheetByName(OUTPUT_SHEET_NAME)) {
    ui.alert('Template đã tồn tại. Vui lòng xóa sheet "Input" và "Output" cũ nếu bạn muốn tạo lại.');
    return;
  }

  // --- Create Input Sheet ---
  const inputSheet = ss.insertSheet(INPUT_SHEET_NAME);
  const headersRange = inputSheet.getRange('A1:E1');
  const headers = [['ID', 'Nội dung bài viết', 'Chủ đề chính', 'Ý định tìm kiếm', 'Trạng thái']];
  
  // Apply header values and formatting
  headersRange.setValues(headers)
              .setFontWeight('bold')
              .setBackground('#d9ead3') // Light green background
              .setHorizontalAlignment('center');
  
  // Set column widths
  inputSheet.setColumnWidth(ID_COL, 150);
  inputSheet.setColumnWidth(CONTENT_COL, 500);
  inputSheet.setColumnWidth(TOPIC_COL, 200);
  inputSheet.setColumnWidth(INTENT_COL, 200);
  inputSheet.setColumnWidth(STATUS_COL, 120);

  // Set wrap strategies
  inputSheet.getRange('A2:A').setWrapStrategy(SpreadsheetApp.WrapStrategy.CLIP); // Clip for ID
  inputSheet.getRange('B2:E').setWrapStrategy(SpreadsheetApp.WrapStrategy.WRAP); // Wrap for other columns

  // Create dropdown for Status column
  const statusRule = SpreadsheetApp.newDataValidation()
      .requireValueInList(['Chờ duyệt', 'Đang xử lý', 'Thành công', 'Lỗi'], true)
      .setAllowInvalid(false)
      .build();
  inputSheet.getRange('E2:E').setDataValidation(statusRule);
  
  // Freeze header row
  inputSheet.setFrozenRows(1);

  // --- Add Conditional Formatting for Status Column ---
  const statusRange = inputSheet.getRange('E2:E');
  const rules = [
    SpreadsheetApp.newConditionalFormatRule()
      .whenTextEqualTo('Chờ duyệt')
      .setBackground('#fff2cc') // Light yellow
      .setRanges([statusRange])
      .build(),
    SpreadsheetApp.newConditionalFormatRule()
      .whenTextEqualTo('Đang xử lý')
      .setBackground('#cfe2f3') // Light blue
      .setRanges([statusRange])
      .build(),
    SpreadsheetApp.newConditionalFormatRule()
      .whenTextEqualTo('Thành công')
      .setBackground('#d9ead3') // Light green
      .setRanges([statusRange])
      .build(),
    SpreadsheetApp.newConditionalFormatRule()
      .whenTextEqualTo('Lỗi')
      .setBackground('#f4cccc') // Light red
      .setRanges([statusRange])
      .build()
  ];
  const sheetRules = inputSheet.getConditionalFormatRules();
  inputSheet.setConditionalFormatRules(sheetRules.concat(rules));


  // --- Create Output Sheet ---
  const outputSheet = ss.insertSheet(OUTPUT_SHEET_NAME);
  const outputHeadersRange = outputSheet.getRange('A1:D1');
  const outputHeaders = [['ID Input', 'Kết quả Phân tích', 'Nội dung đã tối ưu', 'Thời gian xử lý']];
  
  // Apply header values and formatting
  outputHeadersRange.setValues(outputHeaders)
                    .setFontWeight('bold')
                    .setBackground('#d9ead3') // Light green background
                    .setHorizontalAlignment('center');

  // Set column widths
  outputSheet.setColumnWidth(1, 150);
  outputSheet.setColumnWidth(2, 500);
  outputSheet.setColumnWidth(3, 500);
  outputSheet.setColumnWidth(4, 150);
  
  // Set wrap strategies
  outputSheet.getRange('A2:A').setWrapStrategy(SpreadsheetApp.WrapStrategy.CLIP);
  outputSheet.getRange('B2:D').setWrapStrategy(SpreadsheetApp.WrapStrategy.WRAP);

  // Freeze header row
  outputSheet.setFrozenRows(1);
  
  ui.alert('Đã tạo thành công template làm việc.');
}

/**
 * Adds a new row to the Input sheet with a unique ID and default status.
 */
function addNewRow() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(INPUT_SHEET_NAME);
  if (!sheet) {
    SpreadsheetApp.getUi().alert('Không tìm thấy sheet "Input". Vui lòng tạo template trước.');
    return;
  }
  
  const lastRow = sheet.getLastRow();
  const newRow = lastRow + 1;
  
  // Generate UUID and set default status
  sheet.getRange(newRow, ID_COL).setValue(Utilities.getUuid());
  sheet.getRange(newRow, STATUS_COL).setValue('Chờ duyệt');
  
  // Activate the content cell for immediate input
  sheet.getRange(newRow, CONTENT_COL).activate();
}


// --- API CALL & PROCESSING LOGIC ---

/**
 * Finds the first row with 'Chờ duyệt' status and processes it.
 */
function processFirstPendingRow() {
  const ui = SpreadsheetApp.getUi();
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(INPUT_SHEET_NAME);
  if (!sheet) {
    ui.alert('Không tìm thấy sheet "Input". Vui lòng tạo template trước.');
    return;
  }

  // Find the first pending row
  const statusRange = sheet.getRange(2, STATUS_COL, sheet.getLastRow() - 1, 1);
  const statusValues = statusRange.getValues();
  let targetRow = -1;

  for (let i = 0; i < statusValues.length; i++) {
    if (statusValues[i][0] === 'Chờ duyệt') {
      targetRow = i + 2; // +2 because range is 1-based and starts from row 2
      break;
    }
  }

  if (targetRow === -1) {
    ui.alert('Không có nội dung nào đang ở trạng thái "Chờ duyệt".');
    return;
  }

  const statusCell = sheet.getRange(targetRow, STATUS_COL);
  
  try {
    // Mark as processing to prevent re-triggering
    statusCell.setValue('Đang xử lý');
    SpreadsheetApp.flush(); // Apply changes immediately

    // Read data from the target row
    const rowData = sheet.getRange(targetRow, 1, 1, 4).getValues()[0];
    const requestData = {
      id: rowData[ID_COL - 1],
      content: rowData[CONTENT_COL - 1],
      main_topic: rowData[TOPIC_COL - 1],
      search_intent: rowData[INTENT_COL - 1]
    };

    // --- INPUT VALIDATION ---
    if (!requestData.content || !requestData.main_topic || !requestData.search_intent) {
      statusCell.setValue('Chờ duyệt'); // Revert status
      ui.alert('Dữ liệu không hợp lệ', 'Vui lòng điền đầy đủ cả 3 cột: Nội dung, Chủ đề chính, và Ý định tìm kiếm.', ui.ButtonSet.OK);
      return; // Stop execution
    }

    // --- Call Backend API ---
    const { clientId, clientSecret } = getClientCredentials();
    const accessToken = getAccessToken(clientId, clientSecret);
    const result = callProcessContentApi(accessToken, requestData);
    
    // --- Handle Success ---
    writeOutputData(requestData.id, result);
    statusCell.setValue('Thành công');
    
  } catch (e) {
    // --- Handle Error ---
    console.error(`Error processing row ${targetRow}:`, e);
    statusCell.setValue('Lỗi');
    // Optionally, write the error message to a notes column
    // sheet.getRange(targetRow, NOTES_COL).setValue(e.message);
    ui.alert('Đã xảy ra lỗi', `Chi tiết: ${e.message}`, ui.ButtonSet.OK);
  }
}

/**
 * Saves the client ID and client secret configuration.
 */
function saveConfiguration(config) {
  try {
    if (!config || !config.clientId || !config.clientSecret) {
      throw new Error("Dữ liệu không hợp lệ. Vui lòng cung cấp cả Client ID và Client Secret.");
    }

    const scriptProperties = PropertiesService.getScriptProperties();
    scriptProperties.setProperty('clientId', config.clientId);
    scriptProperties.setProperty('clientSecret', config.clientSecret);
    
    return { success: true, message: "Cấu hình đã được lưu thành công." };
  } catch (e) {
    console.error("Failed to save configuration: ", e);
    return { success: false, message: `Lỗi khi lưu cấu hình: ${e.message}` };
  }
}

/**
 * Retrieves the current client ID and client secret.
 */
function getConfiguration() {
  try {
    const scriptProperties = PropertiesService.getScriptProperties();
    return {
      clientId: scriptProperties.getProperty('clientId') || '',
      clientSecret: scriptProperties.getProperty('clientSecret') || ''
    };
  } catch (e) {
    console.error("Failed to get configuration: ", e);
    return { clientId: '', clientSecret: '' };
  }
}


/**
 * Retrieves client credentials from Script Properties.
 */
function getClientCredentials() {
  const scriptProperties = PropertiesService.getScriptProperties();
  const clientId = scriptProperties.getProperty('clientId');
  const clientSecret = scriptProperties.getProperty('clientSecret');

  if (!clientId || !clientSecret) {
    throw new Error("Client ID hoặc Client Secret chưa được cấu hình. Vui lòng vào menu 'Công cụ SEO > Cấu hình'.");
  }

  return { clientId, clientSecret };
}

/**
 * Fetches an access token from the backend.
 */
function getAccessToken(clientId, clientSecret) {
  if (!BACKEND_URL) {
    throw new Error("Backend URL chưa được cấu hình trong script.");
  }

  const url = `${BACKEND_URL}/api/auth/token`;
  const payload = { 'client_id': clientId, 'client_secret': clientSecret };
  const options = {
    'method': 'post',
    'contentType': 'application/json',
    'payload': JSON.stringify(payload),
    'muteHttpExceptions': true
  };
  const response = UrlFetchApp.fetch(url, options);
  const responseCode = response.getResponseCode();
  const responseBody = response.getContentText();

  if (responseCode === 200) {
    return JSON.parse(responseBody).access_token;
  }
  throw new Error(`Không thể lấy access token. Lỗi ${responseCode}: ${responseBody}`);
}

/**
 * Calls the main content processing endpoint.
 */
function callProcessContentApi(token, requestData) {
  if (!BACKEND_URL) {
    throw new Error("Backend URL chưa được cấu hình trong script.");
  }
  const url = `${BACKEND_URL}/api/v1/process-content`;
  const userEmail = Session.getActiveUser().getEmail();
  const options = {
    'method': 'post',
    'contentType': 'application/json',
    'headers': { 
      'Authorization': 'Bearer ' + token,
      'X-User-Email': userEmail
    },
    'payload': JSON.stringify(requestData),
    'muteHttpExceptions': true
  };
  const response = UrlFetchApp.fetch(url, options);
  const responseCode = response.getResponseCode();
  const responseBody = response.getContentText();

  if (responseCode === 200) {
    return JSON.parse(responseBody);
  }
  throw new Error(`Lỗi khi xử lý nội dung. Lỗi ${responseCode}: ${responseBody}`);
}

/**
 * Writes the analysis result to the 'Output' sheet.
 */
function writeOutputData(inputId, result) {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(OUTPUT_SHEET_NAME);
  if (!sheet) return;

  let analysisResult = '';
  try {
    // Sửa lỗi: Kiểm tra trực tiếp result.analysis_notes
    if (result && Array.isArray(result.analysis_notes)) {
      // Build a bulleted list from the array of strings
      analysisResult = result.analysis_notes.map(note => `- ${note}`).join('\n');
    } else if (result && result.analysis) { // Fallback cho các cấu trúc khác có thể có
      analysisResult = JSON.stringify(result.analysis, null, 2);
    }
  } catch (e) {
    // Nếu có lỗi xảy ra, ghi lại toàn bộ đối tượng result để debug
    analysisResult = JSON.stringify(result, null, 2);
    console.error("Lỗi khi định dạng kết quả phân tích: ", e);
  }

  const timestamp = new Date();
  const rewrittenContent = result.rewritten_content || ''; // Lấy nội dung đã tối ưu

  // Sửa lỗi: Thêm rewrittenContent vào đúng cột
  sheet.appendRow([inputId, analysisResult, rewrittenContent, timestamp]);
}
