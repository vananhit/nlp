/**
 * @fileoverview This file contains the main entry points for the script, like onOpen.
 */

/**
 * Creates a custom menu in the spreadsheet UI when the spreadsheet is opened.
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  const menu = ui.createMenu(CONFIG.MENU_NAME);
  
  menu.addItem('1. Tạo Template Gợi ý SEO', 'createSeoSuggestionTemplate');
  menu.addItem('2. Thêm dòng Gợi ý SEO mới', 'addNewSeoSuggestionRow');
  menu.addItem('2.1. Tạo câu hỏi gợi ý (Dòng chờ duyệt đầu tiên)', 'generateSurveyQuestions');
  menu.addItem('3. Tạo Gợi ý SEO (Dòng chờ duyệt đầu tiên)', 'processFirstSeoSuggestionRow');
  menu.addSeparator();
  menu.addItem('4. Tạo Template Tạo Bio', 'createBioTemplate');
  menu.addItem('5. Thêm dòng Tạo Bio mới', 'addNewBioRow');
  menu.addItem('5.1. Tạo câu hỏi gợi ý cho Bio (Dòng chờ duyệt đầu tiên)', 'generateBioSurveyQuestions');
  menu.addItem('6. Tạo Bio (Dòng chờ duyệt đầu tiên)', 'processFirstPendingBioRow');
  menu.addSeparator();
  menu.addItem('7. Cấu hình', 'showConfigurationSidebar');
  
  menu.addToUi();
}
