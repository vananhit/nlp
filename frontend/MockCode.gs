/**
 * @OnlyCurrentDoc
 * 
 * --- THIS IS A MOCK VERSION FOR TESTING ---
 * It simulates a 60-second API call and returns a predefined JSON object.
 * 
 */

// --- CONFIGURATION ---
const BACKEND_URL = 'https://control0001.com'; // This is a placeholder for consistency
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
      .createMenu('Công cụ SEO (MOCK)')
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

    // --- Call Backend API (MOCKED) ---
    const result = callProcessContentApi(null, requestData); // Token is not needed for mock
    
    // --- Handle Success ---
    writeOutputData(requestData.id, result);
    statusCell.setValue('Thành công');
    
  } catch (e) {
    // --- Handle Error ---
    console.error(`Error processing row ${targetRow}:`, e);
    statusCell.setValue('Lỗi');
    ui.alert('Đã xảy ra lỗi', `Chi tiết: ${e.message}`, ui.ButtonSet.OK);
  }
}

/**
 * MOCKED version of the API call.
 * This function simulates a 60-second delay and returns a hardcoded JSON object.
 */
function callProcessContentApi(token, requestData) {
  // Simulate a 60-second network delay
  Utilities.sleep(60000);

  // Return the predefined mock data
  const mockResponse = {
    "client_id": "your-client-id.apps.googleusercontent.com",
    "original_content": "Người mua vàng lần đầu vẫn có cơ hội thành công với kim loại quý này.\nTheo các chuyên gia Tập đoàn đầu tư Goldman Sachs (Mỹ), nếu bạn là một nhà đầu tư mới và đang muốn tìm kiếm các kênh đầu tư hiệu quả, có thể tiếp cận với những lựa chọn truyền thống.\n\nCổ phiếu, trái phiếu và bất động sản đều là những kênh đầu tư phổ biến, mang đến cách đơn giản để gia tăng tài sản theo thời gian, đặc biệt là với những người mới bắt đầu.\n\nTuy nhiên, trong bối cảnh kinh tế bất thường hiện nay, khi lạm phát đang tăng trở lại nhưng thị trường chứng khoán lại mạnh mẽ, thì những nhà đầu tư mới này có thể cảm thấy kém tự tin hơn vào các lựa chọn của mình. Đối với một số người, đầu tư vào vàng có thể trở nên hấp dẫn.\n\nVàng được biết đến như một công cụ phòng ngừa lạm phát và đa dạng hóa danh mục đầu tư.\n\nCác chuyên gia Goldman Sachs gợi ý, vàng ít tạo ra thu nhập theo cách cổ phiếu và trái phiếu làm được, mà chủ yếu là một công cụ bảo vệ thu nhập. Do đó, người mua vàng lần đầu nên xem xét các mục tiêu ngắn hạn của mình để quyết định xem vàng có phù hợp và nên đầu tư bao nhiêu vào kim loại quý này.\n\nGiá vàng liên tục thay đổi, có nghĩa là người mua vàng lần đầu sẽ cần chú ý đến các điều kiện thị trường nếu muốn mua vàng với giá thấp hơn hiện tại.\n\nKể từ đầu năm 2024, giá vàng đã liên tục lập kỷ lục mới và không có dấu hiệu giảm mạnh. Do đó, việc chờ đợi một đợt giảm giá lớn để mua vào có thể không phải là một chiến lược hiệu quả. Với mức giá gần 3.400 USD/ounce (109 triệu đồng/lượng) như hiện nay, vàng có thể khá đắt đỏ, gây khó khăn cho những người mua vàng lần đầu với số vốn khiêm tốn.\n\nDo đó, người mua vàng cần hiểu rõ biến động giá gần đây và dự đoán tương lai để xem vàng có thực sự phù hợp với mục tiêu đầu tư tổng thể của mình hay không? Nếu người mua vàng lần đầu có nguồn vốn lớn và muốn đa dạng hóa danh mục đầu tư, vàng có thể là một lựa chọn tốt. Ngược lại, hãy cân nhắc kỹ và tìm hiểu các kênh đầu tư khác trước khi quyết định.\n\nĐối với người mới bắt đầu, vàng có thể đóng một vai trò nhỏ nhưng rất quan trọng trong việc đa dạng hóa danh mục đầu tư, đặc biệt trong bối cảnh kinh tế nhiều biến động như hiện nay. Để thành công, hãy nhớ cân nhắc mục tiêu ngắn hạn và dài hạn để quyết định xem vàng có phù hợp không. Nắm rõ sự biến động của giá vàng và các dự đoán trong tương lai.\n\nVàng là một công cụ giúp bảo vệ tài sản, vì vậy hãy xem xét nó như một phần của kế hoạch đa dạng hóa danh mục đầu tư của bạn. Bằng cách này, người mua vàng lần đầu sẽ nâng cao cơ hội thành công, ngay từ những bước đầu tiên của hành trình đầu tư.\n\nĐáng chú ý, đầu tư vào vàng luôn mang lại những lợi ích lâu dài, bất kể bạn là nhà đầu tư mới hay đã có kinh nghiệm.",
    "rewritten_content": "Tuyệt vời, đây là phiên bản viết lại của bài báo, được tối ưu hóa toàn diện về chất lượng, khả năng đọc và hiệu suất SEO theo các yêu cầu chi tiết đã đề ra.\n\n---\n\n### **Bài viết được viết lại:**\n\n# Kinh nghiệm mua vàng lần đầu: Hướng dẫn chi tiết cho người mới bắt đầu\n\nGiá vàng liên tục lập đỉnh mới khiến nhiều nhà đầu tư lần đầu băn khoăn: Liệu đây có phải thời điểm thích hợp để mua vào? Dù bạn có số vốn khiêm tốn hay dồi dào, việc hiểu rõ thị trường và trang bị kinh nghiệm thực tế là chìa khóa để thành công với kim loại quý này.\n\nBài viết này sẽ cung cấp một hướng dẫn toàn diện, từ việc phân tích xu hướng giá, lựa chọn loại vàng phù hợp, cho đến cách mua và cất giữ an toàn, giúp bạn tự tin hơn trên hành trình đầu tư của mình.\n\n### Tại sao vàng lại hấp dẫn trong bối cảnh hiện nay?\n\nTrong bối cảnh kinh tế nhiều biến động, lạm phát có dấu hiệu tăng trở lại, các kênh đầu tư truyền thống như cổ phiếu hay bất động sản có thể khiến nhà đầu tư mới cảm thấy lo ngại. Lúc này, vàng nổi lên như một lựa chọn hấp dẫn nhờ những vai trò cốt lõi:\n\n*   **\"Hầm trú ẩn\" an toàn:** Khi thị trường tài chính bất ổn, vàng thường giữ hoặc tăng giá trị, trở thành nơi trú ẩn an toàn cho tài sản.\n*   **Công cụ chống lạm phát:** Về dài hạn, giá trị của vàng có xu hướng tăng khi sức mua của tiền giấy giảm do lạm phát.\n*   **Đa dạng hóa danh mục:** Theo các chuyên gia từ Goldman Sachs, vàng không tạo ra thu nhập thường xuyên như cổ tức từ cổ phiếu, mà chủ yếu đóng vai trò **bảo vệ tài sản**. Việc thêm vàng vào danh mục giúp giảm thiểu rủi ro chung.\n\n### Phân tích giá vàng: Mua bây giờ hay chờ đợi?\n\nKể từ đầu năm 2024, giá vàng trong nước liên tục phá vỡ các kỷ lục. Việc chờ đợi một đợt giảm giá sâu có thể không phải là chiến lược khôn ngoan. Tuy nhiên, mức giá cao hiện tại cũng là một rào cản lớn.\n\n**Điểm cần lưu ý về giá vàng tại Việt Nam:**\n*   **Chênh lệch lớn:** Giá vàng miếng SJC trong nước đang cao hơn đáng kể so với giá vàng thế giới. Điều này tạo ra rủi ro khi các chính sách quản lý thị trường của nhà nước có thể thay đổi.\n*   **Xu hướng khó đoán:** Các yếu tố như chính sách tiền tệ của các ngân hàng trung ương lớn, căng thẳng địa chính trị và nhu cầu thị trường đều ảnh hưởng đến giá vàng, khiến việc dự đoán ngắn hạn trở nên khó khăn.\n\n**Vậy nhà đầu tư mới nên làm gì?**\nThay vì cố gắng \"bắt đáy\", hãy cân nhắc chiến lược **trung bình giá (DCA - Dollar-Cost Averaging)**. Tức là, bạn chia nhỏ số vốn và mua vào đều đặn theo từng tháng hoặc quý. Cách này giúp bạn có được mức giá mua trung bình tốt hơn và giảm thiểu rủi ro khi mua tất cả ở một thời điểm giá cao.\n\n### Hướng dẫn thực hành: Người mua lần đầu cần biết gì?\n\nĐây là những kinh nghiệm thực tế mà bất kỳ nhà đầu tư vàng mới nào cũng cần nắm vững.\n\n#### 1. Nên mua loại vàng nào để đầu tư?\n\nKhông phải loại vàng nào cũng có giá trị đầu tư và tích trữ như nhau.\n\n*   **Vàng miếng SJC:** Là thương hiệu vàng quốc gia, có tính thanh khoản cao nhất, dễ dàng mua bán tại mọi tiệm vàng, ngân hàng. Tuy nhiên, giá thường cao hơn các loại vàng khác và có chênh lệch lớn với giá thế giới.\n*   **Vàng nhẫn tròn trơn 9999 (bốn số 9):** Đây là lựa chọn phổ biến cho người có vốn nhỏ. Giá vàng nhẫn bám sát giá thế giới hơn, chi phí gia công thấp, chênh lệch mua-bán không quá lớn. Đây là lựa chọn tối ưu để tích trữ lâu dài.\n*   **Vàng trang sức:** Không phải là lựa chọn tốt để đầu tư vì bạn sẽ phải trả thêm chi phí thiết kế, gia công. Khi bán lại, những chi phí này thường bị mất đi, khiến bạn lỗ nặng.\n\n**Lời khuyên:** Nếu mới bắt đầu với số vốn khiêm tốn, **vàng nhẫn tròn trơn 9999** từ các thương hiệu uy tín là lựa chọn hợp lý nhất.\n\n#### 2. Mua vàng ở đâu uy tín và an toàn?\n\nĐể đảm bảo chất lượng vàng và nhận được hóa đơn đầy đủ, hãy luôn chọn những địa chỉ uy tín:\n\n*   **Các công ty vàng bạc đá quý lớn:** SJC, PNJ, DOJI, Bảo Tín Minh Châu...\n*   **Các ngân hàng thương mại được cấp phép:** Một số ngân hàng có dịch vụ kinh doanh vàng miếng, đảm bảo an toàn tuyệt đối.\n\n**Tuyệt đối tránh:** Mua vàng tại các cửa hàng nhỏ lẻ, không có giấy phép, không cung cấp hóa đơn chứng từ rõ ràng để tránh rủi ro mua phải vàng giả, vàng kém chất lượng.\n\n#### 3. Cất giữ vàng như thế nào cho an toàn?\n\nSau khi mua, việc bảo quản vàng cũng vô cùng quan trọng.\n\n*   **Tại nhà:** Nếu số lượng ít, bạn có thể cất trong két sắt an toàn tại nhà. Ưu điểm là tiện lợi, không tốn phí nhưng rủi ro về trộm cắp cao hơn.\n*   **Gửi tại ngân hàng:** Hầu hết các ngân hàng đều có dịch vụ cho thuê két sắt an toàn với độ bảo mật cao. Bạn sẽ phải trả một khoản phí hàng năm nhưng đổi lại là sự an tâm tuyệt đối.\n\n### Nguyên tắc vàng cho người mới bắt đầu\n\nĐể hành trình đầu tư vàng thành công, hãy ghi nhớ:\n\n1.  **Xác định mục tiêu rõ ràng:** Bạn mua vàng để tích lũy dài hạn, bảo vệ tài sản hay lướt sóng ngắn hạn? Mục tiêu sẽ quyết định chiến lược của bạn.\n2.  **Phân bổ ngân sách hợp lý:** Đừng \"tất tay\" vào vàng. Vàng chỉ nên chiếm một tỷ trọng nhỏ (khoảng 5-15%) trong tổng danh mục đầu tư của bạn để đảm bảo sự đa dạng hóa.\n3.  **Luôn giữ lại hóa đơn:** Hóa đơn mua hàng là bằng chứng giao dịch, giúp việc bán lại sau này thuận lợi và đúng giá trị.\n\n### Kết luận\n\nĐầu tư vàng lần đầu không hề phức tạp nếu bạn có sự chuẩn bị kỹ lưỡng. Vàng không phải là công cụ làm giàu nhanh chóng, mà là một phần quan trọng trong kế hoạch tài chính dài hạn, giúp bảo vệ tài sản của bạn trước những biến động của nền kinh tế.\n\nBằng cách hiểu rõ thị trường, chọn đúng loại vàng, mua ở nơi uy tín và có kế hoạch tích lũy hợp lý, ngay cả những nhà đầu tư mới cũng hoàn toàn có thể thành công với kênh đầu tư an toàn và bền vững này.",
    "analysis": { // Wrapped analysis_notes inside an 'analysis' object to match original structure
        "analysis_notes": [
            "Actionable Insight: While the article's topic is centrally focused on first-time buyers, it should provide more specific analysis of gold price trends and concrete opportunities rather than just high-level strategic advice.",
            "Actionable Insight: The content serves as a strategic overview ('lưu ý') but fails to provide the practical guidance ('kinh nghiệm') a user with this intent seeks, such as what type of gold to buy, where to buy it, and how to store it safely."
        ]
    }
  };
  return mockResponse;
}

/**
 * Writes the analysis result to the 'Output' sheet.
 * This version is updated to write the rewritten_content as well.
 */
function writeOutputData(inputId, result) {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(OUTPUT_SHEET_NAME);
  if (!sheet) return;

  let analysisResult = '';
  try {
    // Check if analysis and analysis_notes exist and if analysis_notes is an array
    if (result && result.analysis && Array.isArray(result.analysis.analysis_notes)) {
      // Build a bulleted list from the array of strings
      analysisResult = result.analysis.analysis_notes.map(note => `- ${note}`).join('\n');
    } else {
      // Fallback to JSON stringify if the structure is not as expected
      analysisResult = JSON.stringify(result.analysis, null, 2);
    }
  } catch (e) {
    // If any error occurs during formatting, stringify the whole result object for debugging
    analysisResult = JSON.stringify(result, null, 2);
    console.error("Error formatting analysis result: ", e);
  }
  
  const rewrittenContent = result.rewritten_content || ''; // Get rewritten content, default to empty string
  const timestamp = new Date();
  
  sheet.appendRow([inputId, analysisResult, rewrittenContent, timestamp]);
}

// --- Helper functions for configuration and real API calls (adapted for new structure) ---

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

function getClientCredentials() {
  const scriptProperties = PropertiesService.getScriptProperties();
  const clientId = scriptProperties.getProperty('clientId');
  const clientSecret = scriptProperties.getProperty('clientSecret');
  if (!clientId || !clientSecret) {
    // In mock mode, we can return dummy values or throw an error.
    // Let's throw to encourage configuration for consistency.
    throw new Error("Client ID hoặc Client Secret chưa được cấu hình. Vui lòng vào menu 'Công cụ SEO > Cấu hình'.");
  }
  return { clientId, clientSecret };
}

function getAccessToken(clientId, clientSecret) {
  // This function is not actively used in mock mode but is kept for structural consistency.
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
