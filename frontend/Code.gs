/**
 * @OnlyCurrentDoc
 */

// --- CONFIGURATION ---
const BACKEND_URL = 'https://control0001.com'; // <--- THAY THẾ BẰNG URL THỰC TẾ
const SEO_INPUT_SHEET_NAME = 'SEO_Input';
const SEO_OUTPUT_SHEET_NAME = 'SEO_Output';
const BIO_INPUT_SHEET_NAME = 'Bio_Input';
const BIO_OUTPUT_SHEET_NAME = 'Bio_Output';


// --- CONSTANTS FOR COLUMN INDEXES (1-based) ---
// For SEO Suggestions
const SEO_ID_COL = 1;
const SEO_KEYWORD_COL = 2;
const SEO_GOAL_COL = 3;
const SEO_AUDIENCE_COL = 4;
const SEO_VOICE_COL = 5;
const SEO_NOTES_COL = 6;
const SEO_NUM_SUGGESTIONS_COL = 7;
const SEO_OUTPUT_FIELDS_COL = 8;
const SEO_LANGUAGE_COL = 9;
const SEO_ARTICLE_TYPE_COL = 10;
const SEO_STATUS_COL = 11;

// For Bio Generation
const BIO_ID_COL = 1;
const BIO_KEYWORD_COL = 2;
const BIO_WEBSITE_COL = 3;
const BIO_NAME_COL = 4;
const BIO_USERNAME_COL = 5;
const BIO_SHORT_DESC_COL = 6;
const BIO_ADDRESS_COL = 7;
const BIO_HOTLINE_COL = 8;
const BIO_ZIPCODE_COL = 9;
const BIO_NUM_ENTITIES_COL = 10;
const BIO_LANGUAGE_COL = 11;
const BIO_STATUS_COL = 12;


// --- UI FUNCTIONS ---

/**
 * Creates a custom menu in the spreadsheet UI.
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  const menu = ui.createMenu('Công cụ SEO');
  
  menu.addItem('1. Tạo Template Gợi ý SEO', 'createSeoSuggestionTemplate');
  menu.addItem('2. Thêm dòng Gợi ý SEO mới', 'addNewSeoSuggestionRow');
  menu.addItem('3. Tạo Gợi ý SEO (Dòng chờ duyệt đầu tiên)', 'processFirstSeoSuggestionRow');
  menu.addSeparator();
  menu.addItem('4. Tạo Template Tạo Bio', 'createBioTemplate');
  menu.addItem('5. Thêm dòng Tạo Bio mới', 'addNewBioRow');
  menu.addItem('6. Tạo Bio (Dòng chờ duyệt đầu tiên)', 'processFirstPendingBioRow');
  menu.addSeparator();
  menu.addItem('7. Cấu hình', 'showConfigurationSidebar');
  
  menu.addToUi();
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


// --- SEO SUGGESTION FUNCTIONS ---

/**
 * Creates the 'SEO_Input' and 'SEO_Output' sheets for the SEO suggestion feature.
 */
function createSeoSuggestionTemplate() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const ui = SpreadsheetApp.getUi();

  if (ss.getSheetByName(SEO_INPUT_SHEET_NAME) || ss.getSheetByName(SEO_OUTPUT_SHEET_NAME)) {
    ui.alert('Template Gợi ý SEO đã tồn tại. Vui lòng xóa sheet "SEO_Input" và "SEO_Output" cũ nếu bạn muốn tạo lại.');
    return;
  }

  // --- Create SEO_Input Sheet ---
  const inputSheet = ss.insertSheet(SEO_INPUT_SHEET_NAME);
  const headers = [[
    'ID', 'Từ khóa chính', 'Mục tiêu Marketing', 'Đối tượng mục tiêu', 
    'Văn phong', 'Ghi chú thêm', 'Số lượng gợi ý', 'Các trường mong muốn', 'Ngôn ngữ', 'Loại bài viết', 'Trạng thái'
  ]];
  const headersRange = inputSheet.getRange('A1:K1');
  
  headersRange.setValues(headers)
              .setFontWeight('bold')
              .setBackground('#d9ead3')
              .setHorizontalAlignment('center');
  
  inputSheet.setColumnWidth(SEO_ID_COL, 150);
  inputSheet.setColumnWidth(SEO_KEYWORD_COL, 200);
  inputSheet.setColumnWidth(SEO_GOAL_COL, 200);
  inputSheet.setColumnWidth(SEO_AUDIENCE_COL, 200);
  inputSheet.setColumnWidth(SEO_VOICE_COL, 150);
  inputSheet.setColumnWidth(SEO_NOTES_COL, 300);
  inputSheet.setColumnWidth(SEO_NUM_SUGGESTIONS_COL, 120);
  inputSheet.setColumnWidth(SEO_OUTPUT_FIELDS_COL, 300);
  inputSheet.setColumnWidth(SEO_LANGUAGE_COL, 120);
  inputSheet.setColumnWidth(SEO_ARTICLE_TYPE_COL, 250);
  inputSheet.setColumnWidth(SEO_STATUS_COL, 120);

  inputSheet.getRange('A2:K').setWrapStrategy(SpreadsheetApp.WrapStrategy.WRAP);
  inputSheet.getRange(2, SEO_ID_COL, inputSheet.getMaxRows() - 1, 1).setWrapStrategy(SpreadsheetApp.WrapStrategy.CLIP);

  const statusRule = SpreadsheetApp.newDataValidation()
      .requireValueInList(['Chờ duyệt', 'Đang xử lý', 'Thành công', 'Lỗi'], true)
      .setAllowInvalid(false)
      .build();
  inputSheet.getRange(2, SEO_STATUS_COL, inputSheet.getMaxRows() - 1, 1).setDataValidation(statusRule);
  
  inputSheet.setFrozenRows(1);

  const statusRange = inputSheet.getRange(2, SEO_STATUS_COL, inputSheet.getMaxRows() - 1, 1);
  const rules = [
    SpreadsheetApp.newConditionalFormatRule().whenTextEqualTo('Chờ duyệt').setBackground('#fff2cc').setRanges([statusRange]).build(),
    SpreadsheetApp.newConditionalFormatRule().whenTextEqualTo('Đang xử lý').setBackground('#cfe2f3').setRanges([statusRange]).build(),
    SpreadsheetApp.newConditionalFormatRule().whenTextEqualTo('Thành công').setBackground('#d9ead3').setRanges([statusRange]).build(),
    SpreadsheetApp.newConditionalFormatRule().whenTextEqualTo('Lỗi').setBackground('#f4cccc').setRanges([statusRange]).build()
  ];
  const sheetRules = inputSheet.getConditionalFormatRules();
  inputSheet.setConditionalFormatRules(sheetRules.concat(rules));

  // --- Create SEO_Output Sheet ---
  const outputSheet = ss.insertSheet(SEO_OUTPUT_SHEET_NAME);
  const outputHeaders = [[
    'ID Input', 'Tiêu đề (title)', 'Mô tả (description)', 'H1', 'Sapo', 'Nội dung (content)', 'Chuyên mục (Categories)', 'Thời gian xử lý'
  ]];
  const outputHeadersRange = outputSheet.getRange('A1:H1');
  
  outputHeadersRange.setValues(outputHeaders)
                    .setFontWeight('bold')
                    .setBackground('#d9ead3')
                    .setHorizontalAlignment('center');

  outputSheet.setColumnWidth(1, 150); // ID Input
  outputSheet.setColumnWidth(2, 300); // Tiêu đề
  outputSheet.setColumnWidth(3, 400); // Mô tả
  outputSheet.setColumnWidth(4, 250); // H1
  outputSheet.setColumnWidth(5, 400); // Sapo
  outputSheet.setColumnWidth(6, 600); // Nội dung
  outputSheet.setColumnWidth(7, 300); // Chuyên mục
  outputSheet.setColumnWidth(8, 150); // Thời gian xử lý
  
  outputSheet.getRange('A2:H').setWrapStrategy(SpreadsheetApp.WrapStrategy.WRAP);
  outputSheet.getRange(2, 1, outputSheet.getMaxRows() - 1, 1).setWrapStrategy(SpreadsheetApp.WrapStrategy.CLIP);

  outputSheet.setFrozenRows(1);
  
  ui.alert('Đã tạo thành công template Gợi ý SEO.');
}

/**
 * Adds a new row to the SEO_Input sheet with default values.
 */
function addNewSeoSuggestionRow() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SEO_INPUT_SHEET_NAME);
  if (!sheet) {
    SpreadsheetApp.getUi().alert('Không tìm thấy sheet "SEO_Input". Vui lòng tạo template trước.');
    return;
  }
  
  const newRow = sheet.getLastRow() + 1;
  
  sheet.getRange(newRow, SEO_ID_COL).setValue(Utilities.getUuid());
  sheet.getRange(newRow, SEO_NUM_SUGGESTIONS_COL).setValue(3);
  sheet.getRange(newRow, SEO_OUTPUT_FIELDS_COL).setValue('title, description, h1, sapo, content');
  sheet.getRange(newRow, SEO_LANGUAGE_COL).setValue('Vietnamese');
  sheet.getRange(newRow, SEO_STATUS_COL).setValue('Chờ duyệt');
  
  sheet.getRange(newRow, SEO_KEYWORD_COL).activate();
}

/**
 * Finds and processes the first pending row in the SEO_Input sheet.
 */
function processFirstSeoSuggestionRow() {
  const ui = SpreadsheetApp.getUi();
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SEO_INPUT_SHEET_NAME);
  if (!sheet) {
    ui.alert('Không tìm thấy sheet "SEO_Input". Vui lòng tạo template trước.');
    return;
  }

  const statusRange = sheet.getRange(2, SEO_STATUS_COL, sheet.getLastRow() - 1, 1);
  const statusValues = statusRange.getValues();
  let targetRow = -1;

  for (let i = 0; i < statusValues.length; i++) {
    if (statusValues[i][0] === 'Chờ duyệt') {
      targetRow = i + 2;
      break;
    }
  }

  if (targetRow === -1) {
    ui.alert('Không có yêu cầu nào đang ở trạng thái "Chờ duyệt".');
    return;
  }

  const statusCell = sheet.getRange(targetRow, SEO_STATUS_COL);
  const rowData = sheet.getRange(targetRow, 1, 1, sheet.getLastColumn()).getValues()[0];
  const keyword = rowData[SEO_KEYWORD_COL - 1];

  // --- VALIDATION ---
  if (!keyword || !keyword.trim()) {
    ui.alert('Lỗi Dữ liệu', 'Vui lòng điền "Từ khóa chính". Trường này không được để trống.', ui.ButtonSet.OK);
    return;
  }
  
  try {
    statusCell.setValue('Đang xử lý');
    SpreadsheetApp.flush();
    
    const outputFieldsStr = rowData[SEO_OUTPUT_FIELDS_COL - 1] || '';
    const outputFields = outputFieldsStr.split(',').map(item => item.trim()).filter(item => item);

    const requestData = {
      id: rowData[SEO_ID_COL - 1],
      keyword: keyword, // Sử dụng biến đã validate
      marketing_goal: rowData[SEO_GOAL_COL - 1],
      target_audience: rowData[SEO_AUDIENCE_COL - 1],
      brand_voice: rowData[SEO_VOICE_COL - 1],
      custom_notes: rowData[SEO_NOTES_COL - 1],
      num_suggestions: parseInt(rowData[SEO_NUM_SUGGESTIONS_COL - 1], 10) || 3,
      output_fields: outputFields.length > 0 ? outputFields : ["title", "description", "h1", "sapo", "content"],
      language: rowData[SEO_LANGUAGE_COL - 1] || 'Vietnamese',
      article_type: rowData[SEO_ARTICLE_TYPE_COL - 1]
    };

    const { clientId, clientSecret } = getClientCredentials();
    const accessToken = getAccessToken(clientId, clientSecret);
    const result = callGenerateSeoSuggestionsApi(accessToken, requestData);
    
    writeSeoOutputData(requestData.id, result);
    statusCell.setValue('Thành công');
    
  } catch (e) {
    console.error(`Error processing SEO suggestion row ${targetRow}:`, e);
    statusCell.setValue('Lỗi');
    ui.alert('Đã xảy ra lỗi', `Chi tiết: ${e.message}`, ui.ButtonSet.OK);
  }
}

/**
 * Calls the SEO suggestion generation endpoint.
 */
function callGenerateSeoSuggestionsApi(token, requestData) {
  if (!BACKEND_URL) {
    throw new Error("Backend URL chưa được cấu hình trong script.");
  }
  const url = `${BACKEND_URL}/api/v1/generate-seo-suggestions`;
  
  const payload = {
      keyword: requestData.keyword,
      marketing_goal: requestData.marketing_goal,
      target_audience: requestData.target_audience,
      brand_voice: requestData.brand_voice,
      custom_notes: requestData.custom_notes,
      num_suggestions: requestData.num_suggestions,
      output_fields: requestData.output_fields,
      language: requestData.language,
      article_type: requestData.article_type
  };

  const userEmail = Session.getActiveUser().getEmail();
  const options = {
    'method': 'post',
    'contentType': 'application/json',
    'headers': { 
      'Authorization': 'Bearer ' + token,
      'X-User-Email': userEmail
    },
    'payload': JSON.stringify(payload),
    'muteHttpExceptions': true
  };

  const response = UrlFetchApp.fetch(url, options);
  const responseCode = response.getResponseCode();
  const responseBody = response.getContentText();

  if (responseCode === 200) {
    return JSON.parse(responseBody);
  }
  throw new Error(`Lỗi khi tạo gợi ý SEO. Lỗi ${responseCode}: ${responseBody}`);
}

/**
 * Writes the SEO suggestion results to the 'SEO_Output' sheet.
 */
function writeSeoOutputData(inputId, result) {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SEO_OUTPUT_SHEET_NAME);
  if (!sheet) return;

  if (result && Array.isArray(result.suggestions)) {
    const timestamp = new Date();
    result.suggestions.forEach(suggestion => {
      // Chuyển mảng categories thành chuỗi, nếu không có thì trả về chuỗi rỗng
      const categoriesText = (suggestion.categories && Array.isArray(suggestion.categories)) 
        ? suggestion.categories.join(', ') 
        : '';

      const row = [
        inputId,
        suggestion.title || '',
        suggestion.description || '',
        suggestion.h1 || '',
        suggestion.sapo || '',
        suggestion.content || '',
        categoriesText,
        timestamp
      ];
      sheet.appendRow(row);
    });
  } else {
    console.error("Kết quả trả về không hợp lệ hoặc không chứa 'suggestions': ", result);
  }
}


// --- BIO GENERATION FUNCTIONS ---

/**
 * Creates the 'Bio_Input' and 'Bio_Output' sheets for the Bio generation feature.
 */
function createBioTemplate() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const ui = SpreadsheetApp.getUi();

  if (ss.getSheetByName(BIO_INPUT_SHEET_NAME) || ss.getSheetByName(BIO_OUTPUT_SHEET_NAME)) {
    ui.alert('Template Tạo Bio đã tồn tại. Vui lòng xóa sheet "Bio_Input" và "Bio_Output" cũ nếu bạn muốn tạo lại.');
    return;
  }

  // --- Create Bio_Input Sheet ---
  const inputSheet = ss.insertSheet(BIO_INPUT_SHEET_NAME);
  const headers = [[
    'ID', 'Keyword (Từ khóa)', 'Website', 'Name (Tên)', 'Username', 
    'Short Description (Mô tả ngắn)', 
    'Address (Địa chỉ)', 'Hotline', 'Zipcode', 'Num Bio Entities (Số lượng Bio)', 'Ngôn ngữ', 'Trạng thái'
  ]];
  const headersRange = inputSheet.getRange('A1:L1');
  
  headersRange.setValues(headers)
              .setFontWeight('bold')
              .setBackground('#d9ead3')
              .setHorizontalAlignment('center');
  
  // Set column widths
  inputSheet.setColumnWidth(BIO_ID_COL, 150);
  inputSheet.setColumnWidth(BIO_KEYWORD_COL, 200);
  inputSheet.setColumnWidth(BIO_WEBSITE_COL, 200);
  inputSheet.setColumnWidth(BIO_NAME_COL, 150);
  inputSheet.setColumnWidth(BIO_USERNAME_COL, 150);
  inputSheet.setColumnWidth(BIO_SHORT_DESC_COL, 300);
  inputSheet.setColumnWidth(BIO_ADDRESS_COL, 250);
  inputSheet.setColumnWidth(BIO_HOTLINE_COL, 120);
  inputSheet.setColumnWidth(BIO_ZIPCODE_COL, 100);
  inputSheet.setColumnWidth(BIO_NUM_ENTITIES_COL, 120);
  inputSheet.setColumnWidth(BIO_LANGUAGE_COL, 120);
  inputSheet.setColumnWidth(BIO_STATUS_COL, 120);

  inputSheet.getRange('A2:L').setWrapStrategy(SpreadsheetApp.WrapStrategy.WRAP);
  inputSheet.getRange(2, BIO_ID_COL, inputSheet.getMaxRows() - 1, 1).setWrapStrategy(SpreadsheetApp.WrapStrategy.CLIP);

  const statusRule = SpreadsheetApp.newDataValidation()
      .requireValueInList(['Chờ duyệt', 'Đang xử lý', 'Thành công', 'Lỗi'], true)
      .setAllowInvalid(false)
      .build();
  inputSheet.getRange(2, BIO_STATUS_COL, inputSheet.getMaxRows() - 1, 1).setDataValidation(statusRule);
  
  inputSheet.setFrozenRows(1);

  const statusRange = inputSheet.getRange(2, BIO_STATUS_COL, inputSheet.getMaxRows() - 1, 1);
  const rules = [
    SpreadsheetApp.newConditionalFormatRule().whenTextEqualTo('Chờ duyệt').setBackground('#fff2cc').setRanges([statusRange]).build(),
    SpreadsheetApp.newConditionalFormatRule().whenTextEqualTo('Đang xử lý').setBackground('#cfe2f3').setRanges([statusRange]).build(),
    SpreadsheetApp.newConditionalFormatRule().whenTextEqualTo('Thành công').setBackground('#d9ead3').setRanges([statusRange]).build(),
    SpreadsheetApp.newConditionalFormatRule().whenTextEqualTo('Lỗi').setBackground('#f4cccc').setRanges([statusRange]).build()
  ];
  const sheetRules = inputSheet.getConditionalFormatRules();
  inputSheet.setConditionalFormatRules(sheetRules.concat(rules));

  // --- Create Bio_Output Sheet ---
  const outputSheet = ss.insertSheet(BIO_OUTPUT_SHEET_NAME);
  const outputHeaders = [[
    'ID Input', 'Name (Tên)', 'Username', 'Website', 'Address (Địa chỉ)', 
    'Hotline', 'Zipcode', 'Hashtag', 'Bio Entities (Các đoạn Bio)', 'Thời gian xử lý'
  ]];
  const outputHeadersRange = outputSheet.getRange('A1:J1');
  
  outputHeadersRange.setValues(outputHeaders)
                    .setFontWeight('bold')
                    .setBackground('#d9ead3')
                    .setHorizontalAlignment('center');

  outputSheet.setColumnWidth(1, 150); // ID
  outputSheet.setColumnWidth(2, 150); // Name
  outputSheet.setColumnWidth(3, 150); // Username
  outputSheet.setColumnWidth(4, 200); // Website
  outputSheet.setColumnWidth(5, 250); // Address
  outputSheet.setColumnWidth(6, 120); // Hotline
  outputSheet.setColumnWidth(7, 100); // Zipcode
  outputSheet.setColumnWidth(8, 250); // Hashtag
  outputSheet.setColumnWidth(9, 500); // Bio Entities
  outputSheet.setColumnWidth(10, 150); // Timestamp
  
  outputSheet.getRange('A2:J').setWrapStrategy(SpreadsheetApp.WrapStrategy.WRAP);
  outputSheet.getRange(2, 1, outputSheet.getMaxRows() - 1, 1).setWrapStrategy(SpreadsheetApp.WrapStrategy.CLIP);

  outputSheet.setFrozenRows(1);
  
  ui.alert('Đã tạo thành công template Tạo Bio.');
}

/**
 * Adds a new row to the Bio_Input sheet with default values.
 */
function addNewBioRow() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(BIO_INPUT_SHEET_NAME);
  if (!sheet) {
    SpreadsheetApp.getUi().alert('Không tìm thấy sheet "Bio_Input". Vui lòng tạo template trước.');
    return;
  }
  
  const newRow = sheet.getLastRow() + 1;
  
  sheet.getRange(newRow, BIO_ID_COL).setValue(Utilities.getUuid());
  sheet.getRange(newRow, BIO_NUM_ENTITIES_COL).setValue(5); // Default to 5 bio entities
  sheet.getRange(newRow, BIO_LANGUAGE_COL).setValue('Vietnamese');
  sheet.getRange(newRow, BIO_STATUS_COL).setValue('Chờ duyệt');
  
  sheet.getRange(newRow, BIO_KEYWORD_COL).activate();
}

/**
 * Finds and processes the first pending row in the Bio_Input sheet.
 */
function processFirstPendingBioRow() {
  const ui = SpreadsheetApp.getUi();
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(BIO_INPUT_SHEET_NAME);
  if (!sheet) {
    ui.alert('Không tìm thấy sheet "Bio_Input". Vui lòng tạo template trước.');
    return;
  }

  const statusRange = sheet.getRange(2, BIO_STATUS_COL, sheet.getLastRow() - 1, 1);
  const statusValues = statusRange.getValues();
  let targetRow = -1;

  for (let i = 0; i < statusValues.length; i++) {
    if (statusValues[i][0] === 'Chờ duyệt') {
      targetRow = i + 2;
      break;
    }
  }

  if (targetRow === -1) {
    ui.alert('Không có yêu cầu nào đang ở trạng thái "Chờ duyệt".');
    return;
  }

  const statusCell = sheet.getRange(targetRow, BIO_STATUS_COL);
  const rowData = sheet.getRange(targetRow, 1, 1, sheet.getLastColumn()).getValues()[0];
  const keyword = rowData[BIO_KEYWORD_COL - 1];
  const website = rowData[BIO_WEBSITE_COL - 1];

  // --- VALIDATION ---
  if (!keyword || !keyword.trim()) {
    ui.alert('Lỗi Dữ liệu', 'Vui lòng điền "Keyword". Trường này không được để trống.', ui.ButtonSet.OK);
    return;
  }
  if (!website || !website.trim()) {
    ui.alert('Lỗi Dữ liệu', 'Vui lòng điền "Website". Trường này không được để trống.', ui.ButtonSet.OK);
    return;
  }

  try {
    statusCell.setValue('Đang xử lý');
    SpreadsheetApp.flush();
    
    const requestData = {
      id: rowData[BIO_ID_COL - 1],
      keyword: keyword, // Sử dụng biến đã validate
      website: website, // Sử dụng biến đã validate
      name: rowData[BIO_NAME_COL - 1],
      username: rowData[BIO_USERNAME_COL - 1],
      short_description: rowData[BIO_SHORT_DESC_COL - 1],
      address: rowData[BIO_ADDRESS_COL - 1],
      hotline: String(rowData[BIO_HOTLINE_COL - 1] || ''),
      zipcode: String(rowData[BIO_ZIPCODE_COL - 1] || ''),
      num_bio_entities: parseInt(rowData[BIO_NUM_ENTITIES_COL - 1], 10) || 5,
      language: rowData[BIO_LANGUAGE_COL - 1] || 'Vietnamese'
    };

    const { clientId, clientSecret } = getClientCredentials();
    const accessToken = getAccessToken(clientId, clientSecret);
    const result = callGenerateBioApi(accessToken, requestData);
    
    writeBioOutputData(requestData.id, result);
    statusCell.setValue('Thành công');
    
  } catch (e) {
    console.error(`Error processing bio generation row ${targetRow}:`, e);
    statusCell.setValue('Lỗi');
    ui.alert('Đã xảy ra lỗi', `Chi tiết: ${e.message}`, ui.ButtonSet.OK);
  }
}

/**
 * Calls the bio generation endpoint.
 */
function callGenerateBioApi(token, requestData) {
  if (!BACKEND_URL) {
    throw new Error("Backend URL chưa được cấu hình trong script.");
  }
  const url = `${BACKEND_URL}/api/v1/generate-bio-entities`;
  
  // Remove id from payload as it's not part of BioGenerationRequest schema
  const payload = { ...requestData };
  delete payload.id;

  const userEmail = Session.getActiveUser().getEmail();
  const options = {
    'method': 'post',
    'contentType': 'application/json',
    'headers': { 
      'Authorization': 'Bearer ' + token,
      'X-User-Email': userEmail
    },
    'payload': JSON.stringify(payload),
    'muteHttpExceptions': true
  };

  const response = UrlFetchApp.fetch(url, options);
  const responseCode = response.getResponseCode();
  const responseBody = response.getContentText();

  if (responseCode === 200) {
    return JSON.parse(responseBody);
  }
  throw new Error(`Lỗi khi tạo bio. Lỗi ${responseCode}: ${responseBody}`);
}

/**
 * Writes the bio generation results to the 'Bio_Output' sheet.
 */
function writeBioOutputData(inputId, result) {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(BIO_OUTPUT_SHEET_NAME);
  if (!sheet) return;

  if (result && Array.isArray(result.bioEntities)) {
    const timestamp = new Date();
    const bioText = result.bioEntities.join('\n\n---\n\n'); // Join with a separator

    const row = [
      inputId,
      result.name || '',
      result.username || '',
      result.website || '',
      result.address || '',
      result.hotline || '',
      result.zipcode || '',
      result.hashtag || '',
      bioText,
      timestamp
    ];
    sheet.appendRow(row);
  } else {
    console.error("Kết quả trả về không hợp lệ hoặc không chứa 'bioEntities': ", result);
  }
}
