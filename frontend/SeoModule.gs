/**
 * @fileoverview This file contains all functions related to the SEO Suggestion feature.
 */

/**
 * Creates the 'SEO_Input' and 'SEO_Output' sheets for the SEO suggestion feature.
 */
function createSeoSuggestionTemplate() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const ui = SpreadsheetApp.getUi();

  if (ss.getSheetByName(SHEET_NAMES.SEO_INPUT) || ss.getSheetByName(SHEET_NAMES.SEO_OUTPUT)) {
    ui.alert('Template Gợi ý SEO đã tồn tại. Vui lòng xóa sheet "SEO_Input" và "SEO_Output" cũ nếu bạn muốn tạo lại.');
    return;
  }

  // --- Create SEO_Input Sheet ---
  const inputSheet = ss.insertSheet(SHEET_NAMES.SEO_INPUT);
  const headers = [[
    'ID', 'Từ khóa chính', 'Tên Công ty/Thương hiệu', 'Website', 'Mô tả ngắn',
    'Mục tiêu Marketing', 'Đối tượng mục tiêu', 'Văn phong', 'Số lượng gợi ý', 
    'Các trường mong muốn', 'Ngôn ngữ', 'Loại bài viết', 'Trạng thái', 'Thông tin bổ sung'
  ]];
  const headersRange = inputSheet.getRange('A1:N1');
  
  headersRange.setValues(headers)
              .setFontWeight('bold')
              .setBackground('#d9ead3')
              .setHorizontalAlignment('center');
  
  inputSheet.setColumnWidth(SEO_INPUT_COLS.ID, 150);
  inputSheet.setColumnWidth(SEO_INPUT_COLS.KEYWORD, 200);
  inputSheet.setColumnWidth(SEO_INPUT_COLS.COMPANY_NAME, 200);
  inputSheet.setColumnWidth(SEO_INPUT_COLS.WEBSITE, 200);
  inputSheet.setColumnWidth(SEO_INPUT_COLS.SHORT_DESC, 300);
  inputSheet.setColumnWidth(SEO_INPUT_COLS.GOAL, 200);
  inputSheet.setColumnWidth(SEO_INPUT_COLS.AUDIENCE, 200);
  inputSheet.setColumnWidth(SEO_INPUT_COLS.VOICE, 150);
  inputSheet.setColumnWidth(SEO_INPUT_COLS.NUM_SUGGESTIONS, 120);
  inputSheet.setColumnWidth(SEO_INPUT_COLS.OUTPUT_FIELDS, 300);
  inputSheet.setColumnWidth(SEO_INPUT_COLS.LANGUAGE, 120);
  inputSheet.setColumnWidth(SEO_INPUT_COLS.ARTICLE_TYPE, 250);
  inputSheet.setColumnWidth(SEO_INPUT_COLS.STATUS, 120);
  inputSheet.setColumnWidth(SEO_INPUT_COLS.PRODUCT_INFO, 400);


  inputSheet.getRange('A2:N').setWrapStrategy(SpreadsheetApp.WrapStrategy.WRAP);
  inputSheet.getRange(2, SEO_INPUT_COLS.ID, inputSheet.getMaxRows() - 1, 1).setWrapStrategy(SpreadsheetApp.WrapStrategy.CLIP);

  const statusRule = SpreadsheetApp.newDataValidation()
      .requireValueInList([STATUS.PENDING, STATUS.PROCESSING, STATUS.SUCCESS, STATUS.ERROR], true)
      .setAllowInvalid(false)
      .build();
  inputSheet.getRange(2, SEO_INPUT_COLS.STATUS, inputSheet.getMaxRows() - 1, 1).setDataValidation(statusRule);
  
  inputSheet.setFrozenRows(1);

  const statusRange = inputSheet.getRange(2, SEO_INPUT_COLS.STATUS, inputSheet.getMaxRows() - 1, 1);
  const rules = [
    SpreadsheetApp.newConditionalFormatRule().whenTextEqualTo(STATUS.PENDING).setBackground('#fff2cc').setRanges([statusRange]).build(),
    SpreadsheetApp.newConditionalFormatRule().whenTextEqualTo(STATUS.PROCESSING).setBackground('#cfe2f3').setRanges([statusRange]).build(),
    SpreadsheetApp.newConditionalFormatRule().whenTextEqualTo(STATUS.SUCCESS).setBackground('#d9ead3').setRanges([statusRange]).build(),
    SpreadsheetApp.newConditionalFormatRule().whenTextEqualTo(STATUS.ERROR).setBackground('#f4cccc').setRanges([statusRange]).build()
  ];
  const sheetRules = inputSheet.getConditionalFormatRules();
  inputSheet.setConditionalFormatRules(sheetRules.concat(rules));

  // --- Create SEO_Output Sheet ---
  const outputSheet = ss.insertSheet(SHEET_NAMES.SEO_OUTPUT);
  const outputHeaders = [[
    'ID Input', 'Từ khóa chính', 'Mục tiêu Marketing', 'Tiêu đề (title)', 'Mô tả (description)', 'H1', 'Sapo', 'Nội dung (content)', 'Chuyên mục (Categories)', 'Thời gian xử lý'
  ]];
  const outputHeadersRange = outputSheet.getRange('A1:J1');
  
  outputHeadersRange.setValues(outputHeaders)
                    .setFontWeight('bold')
                    .setBackground('#d9ead3')
                    .setHorizontalAlignment('center');

  outputSheet.setColumnWidth(1, 150); // ID Input
  outputSheet.setColumnWidth(2, 200); // Từ khóa chính
  outputSheet.setColumnWidth(3, 200); // Mục tiêu Marketing
  outputSheet.setColumnWidth(4, 300); // Tiêu đề
  outputSheet.setColumnWidth(5, 400); // Mô tả
  outputSheet.setColumnWidth(6, 250); // H1
  outputSheet.setColumnWidth(7, 400); // Sapo
  outputSheet.setColumnWidth(8, 600); // Nội dung
  outputSheet.setColumnWidth(9, 300); // Chuyên mục
  outputSheet.setColumnWidth(10, 150); // Thời gian xử lý
  
  outputSheet.getRange('A2:J').setWrapStrategy(SpreadsheetApp.WrapStrategy.WRAP);
  outputSheet.getRange(2, 1, outputSheet.getMaxRows() - 1, 1).setWrapStrategy(SpreadsheetApp.WrapStrategy.CLIP);

  outputSheet.setFrozenRows(1);
  
  ui.alert('Đã tạo thành công template Gợi ý SEO.');
}

/**
 * Adds a new row to the SEO_Input sheet with default values.
 */
function addNewSeoSuggestionRow() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAMES.SEO_INPUT);
  if (!sheet) {
    SpreadsheetApp.getUi().alert(`Không tìm thấy sheet "${SHEET_NAMES.SEO_INPUT}". Vui lòng tạo template trước.`);
    return;
  }
  
  const newRow = sheet.getLastRow() + 1;
  
  sheet.getRange(newRow, SEO_INPUT_COLS.ID).setValue(Utilities.getUuid());
  sheet.getRange(newRow, SEO_INPUT_COLS.NUM_SUGGESTIONS).setValue(3);
  sheet.getRange(newRow, SEO_INPUT_COLS.OUTPUT_FIELDS).setValue('title, description, h1, sapo, content');
  sheet.getRange(newRow, SEO_INPUT_COLS.LANGUAGE).setValue('Vietnamese');
  sheet.getRange(newRow, SEO_INPUT_COLS.STATUS).setValue(STATUS.PENDING);
  
  sheet.getRange(newRow, SEO_INPUT_COLS.KEYWORD).activate();
}

/**
 * Finds and processes the first pending row in the SEO_Input sheet.
 */
function processFirstSeoSuggestionRow() {
  SpreadsheetApp.flush(); 
  const ui = SpreadsheetApp.getUi();
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAMES.SEO_INPUT);
  if (!sheet) {
    ui.alert(`Không tìm thấy sheet "${SHEET_NAMES.SEO_INPUT}". Vui lòng tạo template trước.`);
    return;
  }

  const statusRange = sheet.getRange(2, SEO_INPUT_COLS.STATUS, sheet.getLastRow() - 1, 1);
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

  const statusCell = sheet.getRange(targetRow, SEO_INPUT_COLS.STATUS);
  const rowData = sheet.getRange(targetRow, 1, 1, sheet.getLastColumn()).getValues()[0];
  const keyword = rowData[SEO_INPUT_COLS.KEYWORD - 1];

  if (!keyword || !keyword.trim()) {
    ui.alert('Lỗi Dữ liệu', 'Vui lòng điền "Từ khóa chính". Trường này không được để trống.', ui.ButtonSet.OK);
    return;
  }
  
  try {
    statusCell.setValue(STATUS.PROCESSING);
    SpreadsheetApp.flush();
    
    const outputFieldsStr = rowData[SEO_INPUT_COLS.OUTPUT_FIELDS - 1] || '';
    const outputFields = outputFieldsStr.split(',').map(item => item.trim()).filter(item => item);

    const requestData = {
      keyword: keyword,
      marketing_goal: rowData[SEO_INPUT_COLS.GOAL - 1],
      target_audience: rowData[SEO_INPUT_COLS.AUDIENCE - 1],
      brand_voice: rowData[SEO_INPUT_COLS.VOICE - 1],
      num_suggestions: parseInt(rowData[SEO_INPUT_COLS.NUM_SUGGESTIONS - 1], 10) || 3,
      output_fields: outputFields.length > 0 ? outputFields : ["title", "description", "h1", "sapo", "content"],
      language: rowData[SEO_INPUT_COLS.LANGUAGE - 1] || 'Vietnamese',
      article_type: rowData[SEO_INPUT_COLS.ARTICLE_TYPE - 1],
      product_info: rowData[SEO_INPUT_COLS.PRODUCT_INFO - 1]
    };

    const result = callApi_('/api/v1/generate-seo-suggestions', requestData);
    
    writeSeoOutputData_(
      rowData[SEO_INPUT_COLS.ID - 1], 
      rowData[SEO_INPUT_COLS.KEYWORD - 1], 
      rowData[SEO_INPUT_COLS.GOAL - 1], 
      result
    );
    statusCell.setValue(STATUS.SUCCESS);
    
  } catch (e) {
    console.error(`Error processing SEO suggestion row ${targetRow}:`, e);
    statusCell.setValue(STATUS.ERROR);
    ui.alert('Đã xảy ra lỗi', `Chi tiết: ${e.message}`, ui.ButtonSet.OK);
  }
}

/**
 * Writes the SEO suggestion results to the 'SEO_Output' sheet.
 * @private
 */
function writeSeoOutputData_(inputId, keyword, marketingGoal, result) {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAMES.SEO_OUTPUT);
  if (!sheet) return;

  if (result && Array.isArray(result.suggestions)) {
    const timestamp = new Date();
    result.suggestions.forEach(suggestion => {
      const categoriesText = (suggestion.categories && Array.isArray(suggestion.categories))
        ? suggestion.categories.map(cat => `${cat.name} - ${cat.score.toFixed(2)}`).join('\\n')
        : '';

      const row = [
        inputId,
        keyword || '',
        marketingGoal || '',
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

/**
 * Generates survey questions for the first pending row and displays them to the user.
 */
function generateSurveyQuestions() {
  SpreadsheetApp.flush();
  const ui = SpreadsheetApp.getUi();
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAMES.SEO_INPUT);
  if (!sheet) {
    ui.alert(`Không tìm thấy sheet "${SHEET_NAMES.SEO_INPUT}". Vui lòng tạo template trước.`);
    return;
  }

  const statusRange = sheet.getRange(2, SEO_INPUT_COLS.STATUS, sheet.getLastRow() - 1, 1);
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
  
  // --- Lấy dữ liệu từ các cột mới ---
  const keyword = rowData[SEO_INPUT_COLS.KEYWORD - 1];
  const companyName = rowData[SEO_INPUT_COLS.COMPANY_NAME - 1];
  const website = rowData[SEO_INPUT_COLS.WEBSITE - 1];
  const shortDesc = rowData[SEO_INPUT_COLS.SHORT_DESC - 1];
  const language = rowData[SEO_INPUT_COLS.LANGUAGE - 1] || 'Vietnamese';

  // --- Kiểm tra dữ liệu đầu vào ---
  if (!keyword || !keyword.trim()) {
    ui.alert('Lỗi Dữ liệu', `Dòng ${targetRow}: Vui lòng điền "Từ khóa chính".`, ui.ButtonSet.OK);
    return;
  }
  if (!companyName || !companyName.trim()) {
    ui.alert('Lỗi Dữ liệu', `Dòng ${targetRow}: Vui lòng điền "Tên Công ty/Thương hiệu".`, ui.ButtonSet.OK);
    return;
  }
  if (!website || !website.trim()) {
    ui.alert('Lỗi Dữ liệu', `Dòng ${targetRow}: Vui lòng điền "Website".`, ui.ButtonSet.OK);
    return;
  }
  if (!shortDesc || !shortDesc.trim()) {
    ui.alert('Lỗi Dữ liệu', `Dòng ${targetRow}: Vui lòng điền "Mô tả ngắn".`, ui.ButtonSet.OK);
    return;
  }

  try {
    // --- Chuẩn bị dữ liệu gửi đi ---
    const requestData = {
      keyword: keyword,
      name: companyName,
      website: website,
      short_description: shortDesc,
      language: language
    };

    // Show a loading message
    SpreadsheetApp.getActiveSpreadsheet().toast('Đang tạo câu hỏi, vui lòng chờ...', 'Thông báo', -1);

    const result = callApi_('/api/v1/generate-seo-survey', requestData);
    
    // Remove the loading message
    SpreadsheetApp.getActiveSpreadsheet().toast('Đã tạo xong!', 'Thành công', 5);

    if (result && Array.isArray(result.questions)) {
      const questionsText = "Gợi ý câu hỏi để bạn cung cấp thông tin:\n\n" + result.questions.join('\n') + 
                            "\n\n--> Vui lòng trả lời các câu hỏi này và dán câu trả lời vào cột 'Thông tin bổ sung'.";
      
      // Sử dụng preformatted text để giữ nguyên định dạng
      const htmlOutput = HtmlService.createHtmlOutput('<pre>' + escapeHtml(questionsText) + '</pre>')
          .setWidth(600)
          .setHeight(400);
      ui.showModalDialog(htmlOutput, 'Câu hỏi gợi ý');

    } else {
      throw new Error("API không trả về danh sách câu hỏi hợp lệ.");
    }

  } catch (e) {
    console.error(`Error generating survey for row ${targetRow}:`, e);
    SpreadsheetApp.getActiveSpreadsheet().toast('Đã xảy ra lỗi.', 'Lỗi', 5);
    ui.alert('Đã xảy ra lỗi', `Chi tiết: ${e.message}`, ui.ButtonSet.OK);
  }
}

/**
 * Helper function to escape HTML characters for display in HtmlService.
 * @param {string} text The text to escape.
 * @return {string} The escaped text.
 */
function escapeHtml(text) {
  if (text == null) return '';
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

