/**
 * @fileoverview This file contains functions related to the configuration sidebar.
 */

/**
 * Shows the configuration sidebar.
 * This function is called from the custom menu.
 */
function showConfigurationSidebar() {
  const html = HtmlService.createHtmlOutputFromFile('Sidebar')
      .setTitle('Cấu hình Kết nối')
      .setWidth(300);
  SpreadsheetApp.getUi().showSidebar(html);
}

/**
 * Saves the client ID and client secret configuration.
 * This function is called from the sidebar's client-side script.
 * @param {object} config An object with clientId and clientSecret properties.
 * @returns {object} A result object with success status and a message.
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
 * This function is called from the sidebar's client-side script.
 * @returns {object} An object with the saved clientId and clientSecret.
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
