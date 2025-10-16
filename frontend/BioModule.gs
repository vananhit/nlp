/**
 * @fileoverview This file contains all functions related to the Bio Generation feature.
 */

/**
 * Creates the 'Bio_Input' and 'Bio_Output' sheets for the Bio generation feature.
 */
function createBioTemplate() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const ui = SpreadsheetApp.getUi();

  if (ss.getSheetByName(SHEET_NAMES.BIO_INPUT) || ss.getSheetByName(SHEET_NAMES.BIO_OUTPUT)) {
    ui.alert('Template Tạo Bio đã tồn tại. Vui lòng xóa sheet "Bio_Input" và "Bio_Output" cũ nếu bạn muốn tạo lại.');
    return;
  }

  // --- Create Bio_Input Sheet ---
  const inputSheet = ss.insertSheet(SHEET_NAMES.BIO_INPUT);
  const headers = [[
    'ID', 'Keyword (Từ khóa)', 'Website', 'Name (Tên)', 'Username', 
    'Short Description (Mô tả ngắn)', 
    'Address (Địa chỉ)', 'Hotline', 'Zipcode', 'Num Bio Entities (Số lượng Bio)', 'Ngôn ngữ', 'Trạng thái', 'Bối cảnh thực thể (Entity Context)'
  ]];
  const headersRange = inputSheet.getRange('A1:M1');
  
  headersRange.setValues(headers)
              .setFontWeight('bold')
              .setBackground('#d9ead3')
              .setHorizontalAlignment('center');
  
  inputSheet.setColumnWidth(BIO_INPUT_COLS.ID, 150);
  inputSheet.setColumnWidth(BIO_INPUT_COLS.KEYWORD, 200);
  inputSheet.setColumnWidth(BIO_INPUT_COLS.WEBSITE, 200);
  inputSheet.setColumnWidth(BIO_INPUT_COLS.NAME, 150);
  inputSheet.setColumnWidth(BIO_INPUT_COLS.USERNAME, 150);
  inputSheet.setColumnWidth(BIO_INPUT_COLS.SHORT_DESC, 300);
  inputSheet.setColumnWidth(BIO_INPUT_COLS.ADDRESS, 250);
  inputSheet.setColumnWidth(BIO_INPUT_COLS.HOTLINE, 120);
  inputSheet.setColumnWidth(BIO_INPUT_COLS.ZIPCODE, 100);
  inputSheet.setColumnWidth(BIO_INPUT_COLS.NUM_ENTITIES, 120);
  inputSheet.setColumnWidth(BIO_INPUT_COLS.LANGUAGE, 120);
  inputSheet.setColumnWidth(BIO_INPUT_COLS.STATUS, 120);
  inputSheet.setColumnWidth(BIO_INPUT_COLS.ENTITY_CONTEXT, 400);

  inputSheet.getRange('A2:M').setWrapStrategy(SpreadsheetApp.WrapStrategy.WRAP);
  inputSheet.getRange(2, BIO_INPUT_COLS.ID, inputSheet.getMaxRows() - 1, 1).setWrapStrategy(SpreadsheetApp.WrapStrategy.CLIP);

  const statusRule = SpreadsheetApp.newDataValidation()
      .requireValueInList([STATUS.PENDING, STATUS.PROCESSING, STATUS.SUCCESS, STATUS.ERROR], true)
      .setAllowInvalid(false)
      .build();
  inputSheet.getRange(2, BIO_INPUT_COLS.STATUS, inputSheet.getMaxRows() - 1, 1).setDataValidation(statusRule);
  
  inputSheet.setFrozenRows(1);

  const statusRange = inputSheet.getRange(2, BIO_INPUT_COLS.STATUS, inputSheet.getMaxRows() - 1, 1);
  const rules = [
    SpreadsheetApp.newConditionalFormatRule().whenTextEqualTo(STATUS.PENDING).setBackground('#fff2cc').setRanges([statusRange]).build(),
    SpreadsheetApp.newConditionalFormatRule().whenTextEqualTo(STATUS.PROCESSING).setBackground('#cfe2f3').setRanges([statusRange]).build(),
    SpreadsheetApp.newConditionalFormatRule().whenTextEqualTo(STATUS.SUCCESS).setBackground('#d9ead3').setRanges([statusRange]).build(),
    SpreadsheetApp.newConditionalFormatRule().whenTextEqualTo(STATUS.ERROR).setBackground('#f4cccc').setRanges([statusRange]).build()
  ];
  const sheetRules = inputSheet.getConditionalFormatRules();
  inputSheet.setConditionalFormatRules(sheetRules.concat(rules));

  // --- Create Bio_Output Sheet ---
  const outputSheet = ss.insertSheet(SHEET_NAMES.BIO_OUTPUT);
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
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAMES.BIO_INPUT);
  if (!sheet) {
    SpreadsheetApp.getUi().alert(`Không tìm thấy sheet "${SHEET_NAMES.BIO_INPUT}". Vui lòng tạo template trước.`);
    return;
  }
  
  const newRow = sheet.getLastRow() + 1;
  
  sheet.getRange(newRow, BIO_INPUT_COLS.ID).setValue(Utilities.getUuid());
  sheet.getRange(newRow, BIO_INPUT_COLS.NUM_ENTITIES).setValue(5);
  sheet.getRange(newRow, BIO_INPUT_COLS.LANGUAGE).setValue('Vietnamese');
  sheet.getRange(newRow, BIO_INPUT_COLS.STATUS).setValue(STATUS.PENDING);
  
  sheet.getRange(newRow, BIO_INPUT_COLS.KEYWORD).activate();
}

/**
 * Finds and processes the first pending row in the Bio_Input sheet.
 */
function processFirstPendingBioRow() {
  SpreadsheetApp.flush();
  const ui = SpreadsheetApp.getUi();
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAMES.BIO_INPUT);
  if (!sheet) {
    ui.alert(`Không tìm thấy sheet "${SHEET_NAMES.BIO_INPUT}". Vui lòng tạo template trước.`);
    return;
  }

  const statusRange = sheet.getRange(2, BIO_INPUT_COLS.STATUS, sheet.getLastRow() - 1, 1);
  const statusValues = statusRange.getValues();
  let targetRow = -1;

  for (let i = 0; i < statusValues.length; i++) {
    if (statusValues[i][0] === STATUS.PENDING) {
      targetRow = i + 2;
      break;
    }
  }

  if (targetRow === -1) {
    ui.alert(`Không có yêu cầu nào đang ở trạng thái "${STATUS.PENDING}".`);
    return;
  }

  const statusCell = sheet.getRange(targetRow, BIO_INPUT_COLS.STATUS);
  const rowData = sheet.getRange(targetRow, 1, 1, sheet.getLastColumn()).getValues()[0];
  const keyword = rowData[BIO_INPUT_COLS.KEYWORD - 1];
  const website = rowData[BIO_INPUT_COLS.WEBSITE - 1];

  if (!keyword || !keyword.trim()) {
    ui.alert('Lỗi Dữ liệu', 'Vui lòng điền "Keyword". Trường này không được để trống.', ui.ButtonSet.OK);
    return;
  }
  if (!website || !website.trim()) {
    ui.alert('Lỗi Dữ liệu', 'Vui lòng điền "Website". Trường này không được để trống.', ui.ButtonSet.OK);
    return;
  }

  try {
    statusCell.setValue(STATUS.PROCESSING);
    SpreadsheetApp.flush();
    
    const requestData = {
      keyword: keyword,
      website: website,
      name: rowData[BIO_INPUT_COLS.NAME - 1],
      username: rowData[BIO_INPUT_COLS.USERNAME - 1],
      short_description: rowData[BIO_INPUT_COLS.SHORT_DESC - 1],
      address: rowData[BIO_INPUT_COLS.ADDRESS - 1],
      hotline: String(rowData[BIO_INPUT_COLS.HOTLINE - 1] || ''),
      zipcode: String(rowData[BIO_INPUT_COLS.ZIPCODE - 1] || ''),
      num_bio_entities: parseInt(rowData[BIO_INPUT_COLS.NUM_ENTITIES - 1], 10) || 5,
      language: rowData[BIO_INPUT_COLS.LANGUAGE - 1] || 'Vietnamese',
      entity_context: rowData[BIO_INPUT_COLS.ENTITY_CONTEXT - 1]
    };

    const result = callApi_('/api/v1/generate-bio-entities', requestData);
    
    writeBioOutputData_(rowData[BIO_INPUT_COLS.ID - 1], result);
    statusCell.setValue(STATUS.SUCCESS);
    
  } catch (e) {
    console.error(`Error processing bio generation row ${targetRow}:`, e);
    statusCell.setValue(STATUS.ERROR);
    ui.alert('Đã xảy ra lỗi', `Chi tiết: ${e.message}`, ui.ButtonSet.OK);
  }
}

/**
 * Writes the bio generation results to the 'Bio_Output' sheet.
 * @private
 */
function writeBioOutputData_(inputId, result) {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAMES.BIO_OUTPUT);
  if (!sheet) return;

  if (result && Array.isArray(result.bioEntities)) {
    const timestamp = new Date();
    const bioText = result.bioEntities.join('\\n\\n---\\n\\n');

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

/**
 * Generates survey questions for the Bio feature for the first pending row.
 */
function generateBioSurveyQuestions() {
  SpreadsheetApp.flush();
  const ui = SpreadsheetApp.getUi();
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAMES.BIO_INPUT);
  if (!sheet) {
    ui.alert(`Không tìm thấy sheet "${SHEET_NAMES.BIO_INPUT}". Vui lòng tạo template trước.`);
    return;
  }

  const statusRange = sheet.getRange(2, BIO_INPUT_COLS.STATUS, sheet.getLastRow() - 1, 1);
  const statusValues = statusRange.getValues();
  let targetRow = -1;

  for (let i = 0; i < statusValues.length; i++) {
    if (statusValues[i][0] === STATUS.PENDING) {
      targetRow = i + 2;
      break;
    }
  }

  if (targetRow === -1) {
    ui.alert(`Không có yêu cầu nào đang ở trạng thái "${STATUS.PENDING}" để tạo câu hỏi.`);
    return;
  }

  const rowData = sheet.getRange(targetRow, 1, 1, sheet.getLastColumn()).getValues()[0];
  
  try {
    const requestData = {
      keyword: rowData[BIO_INPUT_COLS.KEYWORD - 1],
      website: rowData[BIO_INPUT_COLS.WEBSITE - 1],
      name: rowData[BIO_INPUT_COLS.NAME - 1],
      short_description: rowData[BIO_INPUT_COLS.SHORT_DESC - 1]
    };

    SpreadsheetApp.getActiveSpreadsheet().toast('Đang tạo câu hỏi Bio, vui lòng chờ...', 'Thông báo', -1);

    const result = callApi_('/api/v1/generate-bio-survey', requestData);
    
    SpreadsheetApp.getActiveSpreadsheet().toast('Đã tạo xong!', 'Thành công', 5);

    if (result && typeof result.questions === 'string') {
      const markdownContent = result.questions;

      const htmlTemplate = `
      <!DOCTYPE html>
      <html>
        <head>
          <base target="_top">
          <script src="https://cdnjs.cloudflare.com/ajax/libs/showdown/1.9.1/showdown.min.js"></script>
          <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; padding: 15px; }
            h1, h2, h3 { border-bottom: 1px solid #ccc; padding-bottom: 5px; }
            ul, ol { padding-left: 20px; }
            code { background-color: #f4f4f4; padding: 2px 4px; border-radius: 3px; }
            pre { background-color: #f4f4f4; padding: 10px; border-radius: 3px; white-space: pre-wrap; }
            blockquote { border-left: 3px solid #ccc; padding-left: 10px; color: #666; }
          </style>
        </head>
        <body>
          <div id="content"></div>
          <p><em>--> Vui lòng trả lời các câu hỏi này và dán câu trả lời vào cột 'Bối cảnh thực thể (Entity Context)'.</em></p>
          <script>
            const markdownContent = ${JSON.stringify(markdownContent)};
            const converter = new showdown.Converter({tables: true, strikethrough: true, tasklists: true});
            const html = converter.makeHtml(markdownContent);
            document.getElementById('content').innerHTML = html;
          </script>
        </body>
      </html>
    `;

      const htmlOutput = HtmlService.createHtmlOutput(htmlTemplate)
          .setWidth(800)
          .setHeight(600);
      ui.showModalDialog(htmlOutput, 'Câu hỏi gợi ý cho Bio (Xem trước)');

    } else {
      throw new Error("API không trả về nội dung câu hỏi hợp lệ.");
    }

  } catch (e) {
    console.error(`Error generating bio survey for row ${targetRow}:`, e);
    SpreadsheetApp.getActiveSpreadsheet().toast('Đã xảy ra lỗi.', 'Lỗi', 5);
    ui.alert('Đã xảy ra lỗi', `Chi tiết: ${e.message}`, ui.ButtonSet.OK);
  }
}
