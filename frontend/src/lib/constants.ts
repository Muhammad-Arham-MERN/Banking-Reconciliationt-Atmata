/*
 * بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ
 * Theme Constants and Configuration
 * Banking Reconciliation System Frontend
 */

/**
 * Peach-red theme color palette
 * Based on specification requirement for warm, welcoming interface
 */
export const THEME_COLORS = {
  // Primary peach-red colors
  primary: '#E57373', // Light peach-red
  primaryHover: '#EF5350', // Darker peach-red for hover states
  primaryLight: '#FFCDD2', // Very light peach for backgrounds
  primaryDark: '#E53935', // Dark peach-red for emphasis

  // Secondary accent colors
  accent: '#FF8A65', // Peach accent
  accentHover: '#FF7043', // Darker accent for hover

  // Status colors
  success: '#66BB6A', // Green for success states
  warning: '#FFA726', // Orange for warnings
  error: '#EF5350', // Red for errors
  info: '#42A5F5', // Blue for information

  // Neutral colors
  background: '#FFFFFF', // White background
  surface: '#F5F5F5', // Light gray for surfaces
  border: '#E0E0E0', // Gray borders
  text: '#212121', // Dark gray text
  textSecondary: '#757575', // Secondary text color
  textLight: '#FFFFFF', // White text for dark backgrounds

  // Upload zone specific colors
  uploadZoneBorder: '#FFCDD2', // Light peach border for upload zones
  uploadZoneBackground: '#FFEBEE', // Very light peach background
  uploadZoneHover: '#FFCDD2', // Slightly darker on hover
  uploadZoneActive: '#FF8A65', // Active drag state

  // Validation colors
  valid: '#66BB6A', // Green for valid inputs
  invalid: '#EF5350', // Red for invalid inputs
  pending: '#FFA726', // Orange for pending validation
} as const;

/**
 * File validation constraints
 * Based on specification requirements
 */
export const FILE_VALIDATION = {
  // File size limits (in bytes)
  MAX_FILE_SIZE: 50 * 1024 * 1024, // 50MB
  WARNING_FILE_SIZE: 10 * 1024 * 1024, // 10MB (show warning)

  // Allowed file types
  BANK_STATEMENT_TYPES: ['application/pdf'] as const,
  COMPANY_DATA_TYPES: [
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-excel'
  ] as const,

  // File extensions
  BANK_EXTENSIONS: ['.pdf'] as const,
  COMPANY_EXTENSIONS: ['.xlsx', '.xls'] as const,

  // Validation messages
  ERROR_MESSAGES: {
    INVALID_BANK_TYPE: 'Only PDF files are accepted for bank statements',
    INVALID_COMPANY_TYPE: 'Only Excel files (.xlsx, .xls) are accepted for company data',
    FILE_TOO_LARGE: 'File size exceeds 50MB limit. Please compress or split the file.',
    FILE_TOO_LARGE_WARNING: 'Large file detected (>10MB). Upload may take longer.',
    CORRUPTED_FILE: 'File appears to be corrupted or unreadable',
    NO_FILE: 'No file selected',
    EMPTY_FILE: 'File is empty',
  } as const,

  // Success messages
  SUCCESS_MESSAGES: {
    FILE_UPLOADED: 'File uploaded successfully',
    FILE_VALIDATED: 'File validated successfully',
    FILE_READY: 'File ready for processing',
  } as const,
} as const;

/**
 * Column mapping format options
 * Based on specification requirements
 */
export const FORMAT_OPTIONS = [
  {
    value: 'debit-plus-credit' as const,
    label: 'Debit + Credit',
    description: 'Single column with positive/negative values',
    fieldCount: 3,
    fields: ['transactionDateColumn', 'debitPlusCreditColumn', 'transactionDetailsColumn'],
  },
  {
    value: 'debit-pipe-credit' as const,
    label: 'Debit | Credit',
    description: 'Separate columns for debit and credit amounts',
    fieldCount: 4,
    fields: ['transactionDateColumn', 'debitColumn', 'creditColumn', 'transactionDetailsColumn'],
  },
] as const;

/**
 * Form field labels and placeholders
 * Provides consistent text across the application
 */
export const FIELD_LABELS = {
  // Bank upload zone
  BANK_UPLOAD_TITLE: 'Bank Statement',
  BANK_UPLOAD_DESCRIPTION: 'Upload PDF bank statement',
  BANK_UPLOAD_DROP_TEXT: 'Drop PDF file here or click to browse',
  BANK_UPLOAD_ACCEPT: '.pdf',

  // Company upload zone
  COMPANY_UPLOAD_TITLE: 'Company Data',
  COMPANY_UPLOAD_DESCRIPTION: 'Upload Excel company data file',
  COMPANY_UPLOAD_DROP_TEXT: 'Drop Excel file here or click to browse',
  COMPANY_UPLOAD_ACCEPT: '.xlsx, .xls',

  // Format selector
  FORMAT_SELECTOR_LABEL: 'Select Data Format',
  FORMAT_SELECTOR_PLACEHOLDER: 'Choose your company data format',

  SHEET_NAME_LABEL: 'Excel Sheet Name',
  SHEET_NAME_PLACEHOLDER: 'e.g., Sheet1, May-26',

  // Column mapping fields (debit+credit format)
  TRANSACTION_DATE_COLUMN_LABEL: 'Transaction Date Column',
  TRANSACTION_DATE_COLUMN_PLACEHOLDER: 'e.g., Date, Transaction Date',
  DEBIT_PLUS_CREDIT_COLUMN_LABEL: 'Debit + Credit Column',
  DEBIT_PLUS_CREDIT_COLUMN_PLACEHOLDER: 'e.g., Deb./Cred. (LC), Amount',
  TRANSACTION_DETAILS_COLUMN_LABEL: 'Transaction Details Column',
  TRANSACTION_DETAILS_COLUMN_PLACEHOLDER: 'e.g., Description, Memo, Notes',

  // Column mapping fields (debit|credit format)
  DEBIT_COLUMN_LABEL: 'Debit Column',
  DEBIT_COLUMN_PLACEHOLDER: 'e.g., Debit, Debits',
  CREDIT_COLUMN_LABEL: 'Credit Column',
  CREDIT_COLUMN_PLACEHOLDER: 'e.g., Credit, Credits',

  // Submit button
  SUBMIT_BUTTON_LABEL: 'Submit for Processing',
  SUBMIT_BUTTON_LOADING: 'Processing...',
  SUBMIT_BUTTON_DISABLED: 'Complete all fields to submit',
} as const;

/**
 * Accessibility labels
 * Ensures screen reader compatibility
 */
export const A11Y_LABELS = {
  BANK_UPLOAD_ZONE: 'Bank statement file upload zone',
  COMPANY_UPLOAD_ZONE: 'Company data file upload zone',
  FORMAT_SELECTOR: 'Data format selector dropdown',
  REMOVE_FILE_BUTTON: 'Remove uploaded file',
  SUBMIT_BUTTON: 'Submit form for bank reconciliation processing',
  HELP_TOOLTIP: 'Help information',
} as const;

/**
 * Animation and timing constants
 */
export const ANIMATION_TIMING = {
  DEBOUNCE_DELAY: 300, // Debounce delay for file validation (ms)
  FEEDBACK_DELAY: 1000, // Delay before showing success feedback (ms)
  ERROR_DISPLAY_DURATION: 5000, // How long to show error messages (ms)
  TRANSITION_DURATION: 200, // CSS transition duration (ms)
} as const;

/**
 * File icons mapping
 * Maps file types to icon components or emoji
 */
export const FILE_ICONS = {
  PDF: '📄',
  EXCEL: '📊',
  DEFAULT: '📁',
} as const;

/*
 * وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
 */