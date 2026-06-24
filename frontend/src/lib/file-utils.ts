/*
 * بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ
 * File Validation Utilities
 * Banking Reconciliation System Frontend
 */

import { FILE_VALIDATION, FILE_ICONS } from './constants';
import type { BankStatementFile, CompanyDataFile } from '../types/upload';

/**
 * Validates a bank statement file (PDF only)
 * Checks file type, extension, size, and basic readability
 */
export function validateBankFile(file: File): Omit<BankStatementFile, 'id' | 'uploadedAt'> {
  const validationErrors: string[] = [];

  // Check file type (MIME type)
  if (!FILE_VALIDATION.BANK_STATEMENT_TYPES.includes(file.type as any)) {
    validationErrors.push(FILE_VALIDATION.ERROR_MESSAGES.INVALID_BANK_TYPE);
  }

  // Check file extension
  const fileName = file.name.toLowerCase();
  const hasValidExtension = FILE_VALIDATION.BANK_EXTENSIONS.some(ext =>
    fileName.endsWith(ext)
  );

  if (!hasValidExtension) {
    validationErrors.push(FILE_VALIDATION.ERROR_MESSAGES.INVALID_BANK_TYPE);
  }

  // Check file size
  if (file.size === 0) {
    validationErrors.push(FILE_VALIDATION.ERROR_MESSAGES.EMPTY_FILE);
  } else if (file.size > FILE_VALIDATION.MAX_FILE_SIZE) {
    validationErrors.push(FILE_VALIDATION.ERROR_MESSAGES.FILE_TOO_LARGE);
  }

  // Basic file readability check (try to read first few bytes)
  // Note: This is a basic check. Full PDF validation would require a PDF parser.
  const isValid = validationErrors.length === 0;

  return {
    file,
    name: file.name,
    size: file.size,
    type: file.type,
    isValid: isValid,
    validationErrors: isValid ? undefined : validationErrors,
  };
}

/**
 * Validates a company data file (Excel only)
 * Checks file type, extension, size, and basic readability
 */
export function validateCompanyFile(file: File): Omit<CompanyDataFile, 'id' | 'uploadedAt'> {
  const validationErrors: string[] = [];

  // Check file type (MIME type)
  if (!FILE_VALIDATION.COMPANY_DATA_TYPES.includes(file.type as any)) {
    validationErrors.push(FILE_VALIDATION.ERROR_MESSAGES.INVALID_COMPANY_TYPE);
  }

  // Check file extension
  const fileName = file.name.toLowerCase();
  const hasValidExtension = FILE_VALIDATION.COMPANY_EXTENSIONS.some(ext =>
    fileName.endsWith(ext)
  );

  if (!hasValidExtension) {
    validationErrors.push(FILE_VALIDATION.ERROR_MESSAGES.INVALID_COMPANY_TYPE);
  }

  // Check file size
  if (file.size === 0) {
    validationErrors.push(FILE_VALIDATION.ERROR_MESSAGES.EMPTY_FILE);
  } else if (file.size > FILE_VALIDATION.MAX_FILE_SIZE) {
    validationErrors.push(FILE_VALIDATION.ERROR_MESSAGES.FILE_TOO_LARGE);
  }

  // Basic file readability check
  // Note: This is a basic check. Full Excel validation would require a spreadsheet parser.
  const isValid = validationErrors.length === 0;

  return {
    file,
    name: file.name,
    size: file.size,
    type: file.type,
    isValid: isValid,
    validationErrors: isValid ? undefined : validationErrors,
  };
}

/**
 * Formats file size in human-readable format
 * Converts bytes to KB, MB, or GB as appropriate
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

/**
 * Checks if file size is large enough to show a warning
 * Files over 10MB should trigger a warning about upload time
 */
export function isLargeFile(bytes: number): boolean {
  return bytes > FILE_VALIDATION.WARNING_FILE_SIZE;
}

/**
 * Gets file icon based on file type
 * Returns emoji icon for display in upload zones
 */
export function getFileIcon(fileName: string): string {
  const extension = fileName.toLowerCase().split('.').pop();

  switch (extension) {
    case 'pdf':
      return FILE_ICONS.PDF;
    case 'xlsx':
    case 'xls':
      return FILE_ICONS.EXCEL;
    default:
      return FILE_ICONS.DEFAULT;
  }
}

/**
 * Checks if a file is potentially corrupted
 * This is a basic check - full validation would require file-type specific parsers
 */
export async function isFileCorrupted(file: File): Promise<boolean> {
  try {
    // Try to read the first 4KB of the file
    const firstChunk = file.slice(0, 4096);
    const buffer = await firstChunk.arrayBuffer();

    // Check if we can read the data
    if (buffer.byteLength === 0) {
      return true; // Empty file is considered corrupted
    }

    // Basic validation - if we can read the first chunk, assume not corrupted
    // Full validation would require PDF/Excel parsers
    return false;
  } catch (error) {
    // If we can't read the file at all, it's likely corrupted
    return true;
  }
}

/**
 * Generates a unique ID for file instances
 * Used to track files during the upload session
 */
export function generateFileId(): string {
  return `file-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Creates a BankStatementFile object with validation
 */
export async function createBankStatementFile(file: File): Promise<BankStatementFile> {
  const validationResult = validateBankFile(file);
  const isCorrupted = await isFileCorrupted(file);

  if (isCorrupted) {
    return {
      ...validationResult,
      id: generateFileId(),
      uploadedAt: new Date(),
      isValid: false,
      validationErrors: [
        ...(validationResult.validationErrors || []),
        FILE_VALIDATION.ERROR_MESSAGES.CORRUPTED_FILE,
      ],
    };
  }

  return {
    ...validationResult,
    id: generateFileId(),
    uploadedAt: new Date(),
  };
}

/**
 * Creates a CompanyDataFile object with validation
 */
export async function createCompanyDataFile(file: File): Promise<CompanyDataFile> {
  const validationResult = validateCompanyFile(file);
  const isCorrupted = await isFileCorrupted(file);

  if (isCorrupted) {
    return {
      ...validationResult,
      id: generateFileId(),
      uploadedAt: new Date(),
      isValid: false,
      validationErrors: [
        ...(validationResult.validationErrors || []),
        FILE_VALIDATION.ERROR_MESSAGES.CORRUPTED_FILE,
      ],
    };
  }

  return {
    ...validationResult,
    id: generateFileId(),
    uploadedAt: new Date(),
  };
}

/*
 * وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
 */