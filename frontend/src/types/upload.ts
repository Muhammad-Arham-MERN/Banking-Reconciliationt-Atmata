/*
 * بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ
 * File Upload Type Definitions
 * Banking Reconciliation System Frontend
 */

/**
 * Represents the official bank statement uploaded by the user
 * Serves as the source of truth for reconciliation
 */
export interface BankStatementFile {
  id: string; // Unique identifier for the file instance
  file: File; // Browser File object (PDF format)
  name: string; // File name from file.name
  size: number; // File size in bytes
  type: string; // MIME type: 'application/pdf'
  uploadedAt: Date; // Timestamp when file was uploaded
  isValid: boolean; // Validation status
  validationErrors?: string[]; // Array of error messages if invalid
}

/**
 * Represents the internal financial records from the user's organization in spreadsheet format
 */
export interface CompanyDataFile {
  id: string; // Unique identifier for the file instance
  file: File; // Browser File object (XLSX format)
  name: string; // File name from file.name
  size: number; // File size in bytes
  type: string; // MIME type: Excel MIME type
  uploadedAt: Date; // Timestamp when file was uploaded
  isValid: boolean; // Validation status
  validationErrors?: string[]; // Array of error messages if invalid
}

/**
 * Format type options for column mapping configuration
 */
export type FormatType = 'debit-plus-credit' | 'debit-pipe-credit';

/**
 * Represents the user's specification of how their company data is structured
 * Enables the system to correctly interpret spreadsheet data
 */
export interface ColumnMappingConfiguration {
  formatType: FormatType; // Selected format type
  sheetName: string; // Excel worksheet name

  // Fields for debit+credit format (3 fields)
  debitPlusCreditFields?: {
    transactionDateColumn: string; // Column name for transaction dates
    debitPlusCreditColumn: string; // Combined debit/credit column name
    transactionDetailsColumn: string; // Transaction description/details column
  };

  // Fields for debit|credit format (4 fields)
  debitPipeCreditFields?: {
    transactionDateColumn: string; // Column name for transaction dates
    debitColumn: string; // Separate debit column name
    creditColumn: string; // Separate credit column name
    transactionDetailsColumn: string; // Transaction description/details column
  };

  isComplete: boolean; // Whether all required fields are filled
  validationErrors?: Record<string, string>; // Field-specific error messages
}

/**
 * Represents the complete collection of files and configuration needed to process a reconciliation request
 */
export interface SubmissionPackage {
  id: string; // Unique submission identifier
  bankStatement: BankStatementFile;
  companyData: CompanyDataFile;
  columnMapping: ColumnMappingConfiguration;
  submittedAt: Date; // Timestamp of submission
  status: 'pending' | 'uploading' | 'success' | 'error';
  errorMessage?: string; // Error message if status === 'error'
}

/**
 * Top-level state managed by the main UploadForm component
 */
export interface UploadFormState {
  // File upload states
  bankStatement: BankStatementFile | null;
  companyData: CompanyDataFile | null;

  // Column mapping state
  columnMapping: ColumnMappingConfiguration;

  // Form interaction states
  isSubmitting: boolean;
  submissionStatus: 'idle' | 'success' | 'error';
  submissionError?: string;

  // Drag-and-drop states
  dragOverZone: 'bank' | 'company' | null;
}

/**
 * Form validation state
 */
export interface FormValidationState {
  isBankFileValid: boolean;
  isCompanyFileValid: boolean;
  isColumnMappingComplete: boolean;
  canSubmit: boolean;
}

/*
 * وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
 */