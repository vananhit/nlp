/**
 * @fileoverview This file handles all API communications with the backend.
 */

/**
 * Retrieves client credentials from Script Properties.
 * @returns {{clientId: string, clientSecret: string}} The client credentials.
 * @throws {Error} If credentials are not configured.
 */
function getClientCredentials_() {
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
 * @param {string} clientId The client ID.
 * @param {string} clientSecret The client secret.
 * @returns {string} The access token.
 * @throws {Error} If the token cannot be fetched.
 */
function getAccessToken_(clientId, clientSecret) {
  if (!CONFIG.BACKEND_URL) {
    throw new Error("Backend URL chưa được cấu hình trong script.");
  }

  const url = `${CONFIG.BACKEND_URL}/api/auth/token`;
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
 * A generic function to make API calls to the backend.
 * @param {string} endpoint The API endpoint to call (e.g., '/api/v1/generate-seo-suggestions').
 * @param {object} payload The JSON payload for the request.
 * @returns {object} The JSON response from the API.
 * @throws {Error} If the API call fails.
 */
function callApi_(endpoint, payload) {
  const { clientId, clientSecret } = getClientCredentials_();
  const accessToken = getAccessToken_(clientId, clientSecret);
  
  const url = `${CONFIG.BACKEND_URL}${endpoint}`;
  const userEmail = Session.getActiveUser().getEmail();

  const options = {
    'method': 'post',
    'contentType': 'application/json',
    'headers': { 
      'Authorization': 'Bearer ' + accessToken,
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
  throw new Error(`Lỗi API tại ${endpoint}. Lỗi ${responseCode}: ${responseBody}`);
}
