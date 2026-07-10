/*
 * بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ
 * وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
 * Form Validation Logic
 * Banking Reconciliation System Frontend
 */

import type {
  BankStatementFile,
  CompanyDataFile,
  ColumnMappingConfiguration,
  FormValidationState,
} from '../types/upload';

/**
 * Validates a single text field (Excel column name)
 * Allows any printable characters — headers may include symbols like Deb./Cred. (LC)
 */
export function validateTextField(value: string): { isValid: boolean; error?: string } {
  const trimmedValue = value.trim();

  if (trimmedValue.length === 0) {
    return {
      isValid: false,
      error: 'This field is required',
    };
  }

  if (trimmedValue.length > 100) {
    return {
      isValid: false,
      error: 'Column name too long (maximum 100 characters)',
    };
  }

  return { isValid: true };
}

/**
 * Validates column mapping configuration
 * Checks that all required fields are present and valid
 */
export function validateSheetName(value: string): { isValid: boolean; error?: string } {
  const trimmedValue = value.trim();

  if (trimmedValue.length === 0) {
    return { isValid: false, error: 'Sheet name is required' };
  }

  if (trimmedValue.length > 100) {
    return { isValid: false, error: 'Sheet name too long (maximum 100 characters)' };
  }

  return { isValid: true };
}

export function validateColumnMapping(config: ColumnMappingConfiguration): {
  isValid: boolean;
  errors: Record<string, string>;
} {
  const errors: Record<string, string> = {};
  const { formatType, debitPlusCreditFields, debitPipeCreditFields } = config;

  const sheetValidation = validateSheetName(config.sheetName ?? '');
  if (!sheetValidation.isValid) {
    errors.sheetName = sheetValidation.error!;
  }

  // Validate based on format type
  if (formatType === 'debit-plus-credit') {
    if (!debitPlusCreditFields) {
      errors.debitPlusCreditFields = 'Debit+Credit fields are required';
    } else {
      // Validate transaction date column
      const dateValidation = validateTextField(debitPlusCreditFields.transactionDateColumn);
      if (!dateValidation.isValid) {
        errors.transactionDateColumn = dateValidation.error!;
      }

      // Validate debit+credit column
      const amountValidation = validateTextField(debitPlusCreditFields.debitPlusCreditColumn);
      if (!amountValidation.isValid) {
        errors.debitPlusCreditColumn = amountValidation.error!;
      }

      // Validate transaction details column
      const detailsValidation = validateTextField(debitPlusCreditFields.transactionDetailsColumn);
      if (!detailsValidation.isValid) {
        errors.transactionDetailsColumn = detailsValidation.error!;
      }
    }
  } else if (formatType === 'debit-pipe-credit') {
    if (!debitPipeCreditFields) {
      errors.debitPipeCreditFields = 'Debit|Credit fields are required';
    } else {
      // Validate transaction date column
      const dateValidation = validateTextField(debitPipeCreditFields.transactionDateColumn);
      if (!dateValidation.isValid) {
        errors.transactionDateColumn = dateValidation.error!;
      }

      // Validate debit column
      const debitValidation = validateTextField(debitPipeCreditFields.debitColumn);
      if (!debitValidation.isValid) {
        errors.debitColumn = debitValidation.error!;
      }

      // Validate credit column
      const creditValidation = validateTextField(debitPipeCreditFields.creditColumn);
      if (!creditValidation.isValid) {
        errors.creditColumn = creditValidation.error!;
      }

      // Validate transaction details column
      const detailsValidation = validateTextField(debitPipeCreditFields.transactionDetailsColumn);
      if (!detailsValidation.isValid) {
        errors.transactionDetailsColumn = detailsValidation.error!;
      }
    }
  }

  return {
    isValid: Object.keys(errors).length === 0,
    errors,
  };
}

/**
 * Validates complete form state
 * Checks bank file, company file, and column mapping configuration
 */
export function validateFormState(params: {
  bankStatement: BankStatementFile | null;
  companyData: CompanyDataFile | null;
  columnMapping: ColumnMappingConfiguration;
}): FormValidationState {
  const { bankStatement, companyData, columnMapping } = params;

  // Validate bank statement file
  const isBankFileValid = bankStatement !== null && bankStatement.isValid;

  // Validate company data file
  const isCompanyFileValid = companyData !== null && companyData.isValid;

  // Validate column mapping configuration
  const columnValidation = validateColumnMapping(columnMapping);
  const isColumnMappingComplete = columnValidation.isValid;

  // Overall validation
  const canSubmit = isBankFileValid && isCompanyFileValid && isColumnMappingComplete;

  return {
    isBankFileValid,
    isCompanyFileValid,
    isColumnMappingComplete,
    canSubmit,
  };
}

/**
 * Checks if form can be submitted
 * Convenience function for submit button state
 */
export function canSubmitForm(params: {
  bankStatement: BankStatementFile | null;
  companyData: CompanyDataFile | null;
  columnMapping: ColumnMappingConfiguration;
}): boolean {
  const validation = validateFormState(params);
  return validation.canSubmit;
}

/**
 * Updates column mapping configuration with validation
 * Returns updated config with validation state and errors
 */
export function updateColumnMappingValidation(
  config: ColumnMappingConfiguration
): ColumnMappingConfiguration {
  const validation = validateColumnMapping(config);

  return {
    ...config,
    isComplete: validation.isValid,
    validationErrors: validation.isValid ? undefined : validation.errors,
  };
}

/**
 * Preserves common field values when switching format types
 * Keeps transactionDateColumn and transactionDetailsColumn values
 */
export function preserveCommonFields(
  currentConfig: ColumnMappingConfiguration,
  newFormatType: 'debit-plus-credit' | 'debit-pipe-credit'
): ColumnMappingConfiguration {
  // Extract common field values from current config
  let commonDateColumn = '';
  let commonDetailsColumn = '';

  if (currentConfig.formatType === 'debit-plus-credit' && currentConfig.debitPlusCreditFields) {
    commonDateColumn = currentConfig.debitPlusCreditFields.transactionDateColumn;
    commonDetailsColumn = currentConfig.debitPlusCreditFields.transactionDetailsColumn;
  } else if (currentConfig.formatType === 'debit-pipe-credit' && currentConfig.debitPipeCreditFields) {
    commonDateColumn = currentConfig.debitPipeCreditFields.transactionDateColumn;
    commonDetailsColumn = currentConfig.debitPipeCreditFields.transactionDetailsColumn;
  }

  // Create new config with preserved common fields
  if (newFormatType === 'debit-plus-credit') {
    return {
      formatType: newFormatType,
      sheetName: currentConfig.sheetName ?? 'Sheet1',
      aggregatedTotalColumn: currentConfig.aggregatedTotalColumn ?? '',
      debitPlusCreditFields: {
        transactionDateColumn: commonDateColumn,
        debitPlusCreditColumn: '',
        transactionDetailsColumn: commonDetailsColumn,
      },
      isComplete: false,
    };
  } else {
    return {
      formatType: newFormatType,
      sheetName: currentConfig.sheetName ?? 'Sheet1',
      aggregatedTotalColumn: currentConfig.aggregatedTotalColumn ?? '',
      debitPipeCreditFields: {
        transactionDateColumn: commonDateColumn,
        debitColumn: '',
        creditColumn: '',
        transactionDetailsColumn: commonDetailsColumn,
      },
      isComplete: false,
    };
  }
}

/**
 * Gets error message for a specific field
 * Returns undefined if no error
 */
export function getFieldError(
  fieldName: string,
  validationErrors: Record<string, string> | undefined
): string | undefined {
  return validationErrors?.[fieldName];
}

/**
 * Checks if a specific field has an error
 */
export function hasFieldError(
  fieldName: string,
  validationErrors: Record<string, string> | undefined
): boolean {
  return validationErrors?.[fieldName] !== undefined;
}

/*
 * وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
 */