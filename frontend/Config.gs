/**
 * @fileoverview This file contains all the configuration constants for the project.
 */

// --- GENERAL CONFIGURATION ---
const CONFIG = {
  BACKEND_URL: 'https://control0001.com', // <--- THAY THẾ BẰNG URL THỰC TẾ
  MENU_NAME: 'Công cụ SEO'
};

// --- SHEET NAMES ---
const SHEET_NAMES = {
  SEO_INPUT: 'SEO_Input',
  SEO_OUTPUT: 'SEO_Output',
  BIO_INPUT: 'Bio_Input',
  BIO_OUTPUT: 'Bio_Output'
};

// --- STATUS VALUES ---
const STATUS = {
  PENDING: 'Chờ duyệt',
  PROCESSING: 'Đang xử lý',
  SUCCESS: 'Thành công',
  ERROR: 'Lỗi'
};


// --- COLUMN INDEXES (1-based) ---

const SEO_INPUT_COLS = {
  ID: 1,
  KEYWORD: 2,
  COMPANY_NAME: 3,
  WEBSITE: 4,
  SHORT_DESC: 5,
  GOAL: 6,
  AUDIENCE: 7,
  VOICE: 8,
  NUM_SUGGESTIONS: 9,
  OUTPUT_FIELDS: 10,
  LANGUAGE: 11,
  ARTICLE_TYPE: 12,
  STATUS: 13,
  PRODUCT_INFO: 14
};

const BIO_INPUT_COLS = {
  ID: 1,
  KEYWORD: 2,
  WEBSITE: 3,
  NAME: 4,
  USERNAME: 5,
  SHORT_DESC: 6,
  ADDRESS: 7,
  HOTLINE: 8,
  ZIPCODE: 9,
  NUM_ENTITIES: 10,
  LANGUAGE: 11,
  STATUS: 12,
  ENTITY_CONTEXT: 13
};
