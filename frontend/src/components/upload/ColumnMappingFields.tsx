/*
 * بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ
 * وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
 * Column Mapping Fields Component
 * Banking Reconciliation System Frontend
 */

'use client';

import React from 'react';
import { FIELD_LABELS } from '../../lib/constants';
import type { ColumnMappingConfiguration } from '../../types/upload';
import { validateTextField, preserveCommonFields } from '../../lib/validation';

interface ColumnMappingFieldsProps {
  config: ColumnMappingConfiguration;
  onConfigChange: (config: ColumnMappingConfiguration) => void;
  disabled?: boolean;
}

/**
 * Column mapping fields component with conditional rendering
 * Shows 3 fields for debit+credit format, 4 fields for debit|credit format
 */
export function ColumnMappingFields({
  config,
  onConfigChange,
  disabled = false,
}: ColumnMappingFieldsProps) {
  // Handle field value changes
  const handleFieldChange = (fieldName: string, value: string) => {
    let updatedConfig: ColumnMappingConfiguration;

    if (fieldName === 'sheetName') {
      updatedConfig = { ...config, sheetName: value };
    } else if (fieldName === 'aggregatedTotalColumn') {
      updatedConfig = { ...config, aggregatedTotalColumn: value };
    } else if (config.formatType === 'debit-plus-credit' && config.debitPlusCreditFields) {
      updatedConfig = {
        ...config,
        debitPlusCreditFields: {
          ...config.debitPlusCreditFields,
          [fieldName]: value,
        },
      };
    } else if (config.formatType === 'debit-pipe-credit' && config.debitPipeCreditFields) {
      updatedConfig = {
        ...config,
        debitPipeCreditFields: {
          ...config.debitPipeCreditFields,
          [fieldName]: value,
        },
      };
    } else {
      return; // Invalid state
    }

    // Update validation
    const validation = validateTextField(value);
    if (!validation.isValid && config.validationErrors) {
      updatedConfig = {
        ...updatedConfig,
        validationErrors: {
          ...config.validationErrors,
          [fieldName]: validation.error!,
        },
      };
    } else if (config.validationErrors && config.validationErrors[fieldName]) {
      const { [fieldName]: _, ...remainingErrors } = config.validationErrors;
      updatedConfig = {
        ...updatedConfig,
        validationErrors: Object.keys(remainingErrors).length > 0 ? remainingErrors : undefined,
      };
    }

    onConfigChange(updatedConfig);
  };

  // Helper to render a text input field
  const renderField = (
    label: string,
    placeholder: string,
    value: string,
    fieldName: string,
    error?: string
  ) => (
    <div className="space-y-1">
      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
        {label}
      </label>
      <input
        type="text"
        value={value}
        onChange={(e) => handleFieldChange(fieldName, e.target.value)}
        disabled={disabled}
        placeholder={placeholder}
        className={`
          w-full px-3 py-2 rounded-lg border-2
          ${error ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : 'border-gray-300 focus:border-[#FF8A65] focus:ring-[#FF8A65] dark:border-gray-700'}
          bg-white text-gray-800 text-sm dark:bg-gray-900 dark:text-gray-100
          focus:ring-2 focus:ring-opacity-50
          transition-all duration-200
          disabled:opacity-50 disabled:cursor-not-allowed
        `}
      />
      {error && (
        <p className="text-xs text-red-600 mt-1">{error}</p>
      )}
    </div>
  );

  // Render fields based on format type
  const renderDebitPlusCreditFields = () => {
    if (!config.debitPlusCreditFields) return null;

    const { transactionDateColumn, debitPlusCreditColumn, transactionDetailsColumn } = config.debitPlusCreditFields;
    const errors = config.validationErrors || {};

    return (
      <div className="space-y-4">
        {renderField(
          FIELD_LABELS.TRANSACTION_DATE_COLUMN_LABEL,
          FIELD_LABELS.TRANSACTION_DATE_COLUMN_PLACEHOLDER,
          transactionDateColumn,
          'transactionDateColumn',
          errors.transactionDateColumn
        )}

        {renderField(
          FIELD_LABELS.DEBIT_PLUS_CREDIT_COLUMN_LABEL,
          FIELD_LABELS.DEBIT_PLUS_CREDIT_COLUMN_PLACEHOLDER,
          debitPlusCreditColumn,
          'debitPlusCreditColumn',
          errors.debitPlusCreditColumn
        )}

        {renderField(
          FIELD_LABELS.TRANSACTION_DETAILS_COLUMN_LABEL,
          FIELD_LABELS.TRANSACTION_DETAILS_COLUMN_PLACEHOLDER,
          transactionDetailsColumn,
          'transactionDetailsColumn',
          errors.transactionDetailsColumn
        )}
      </div>
    );
  };

  const renderDebitPipeCreditFields = () => {
    if (!config.debitPipeCreditFields) return null;

    const { transactionDateColumn, debitColumn, creditColumn, transactionDetailsColumn } = config.debitPipeCreditFields;
    const errors = config.validationErrors || {};

    return (
      <div className="space-y-4">
        {renderField(
          FIELD_LABELS.TRANSACTION_DATE_COLUMN_LABEL,
          FIELD_LABELS.TRANSACTION_DATE_COLUMN_PLACEHOLDER,
          transactionDateColumn,
          'transactionDateColumn',
          errors.transactionDateColumn
        )}

        {renderField(
          FIELD_LABELS.DEBIT_COLUMN_LABEL,
          FIELD_LABELS.DEBIT_COLUMN_PLACEHOLDER,
          debitColumn,
          'debitColumn',
          errors.debitColumn
        )}

        {renderField(
          FIELD_LABELS.CREDIT_COLUMN_LABEL,
          FIELD_LABELS.CREDIT_COLUMN_PLACEHOLDER,
          creditColumn,
          'creditColumn',
          errors.creditColumn
        )}

        {renderField(
          FIELD_LABELS.TRANSACTION_DETAILS_COLUMN_LABEL,
          FIELD_LABELS.TRANSACTION_DETAILS_COLUMN_PLACEHOLDER,
          transactionDetailsColumn,
          'transactionDetailsColumn',
          errors.transactionDetailsColumn
        )}
      </div>
    );
  };

  // Don't render if no format is selected
  if (!config.formatType) {
    return (
      <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg dark:bg-gray-900 dark:border-gray-800">
        <p className="text-sm text-gray-500 text-center dark:text-gray-400">
          Select a data format above to configure column mappings
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-100">
          Column Mapping Configuration
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Specify the column names from your Excel file that correspond to each data field
        </p>
      </div>

      {/* Conditional fields based on format type */}
      {renderField(
        FIELD_LABELS.SHEET_NAME_LABEL,
        FIELD_LABELS.SHEET_NAME_PLACEHOLDER,
        config.sheetName ?? '',
        'sheetName',
        config.validationErrors?.sheetName
      )}

      {config.formatType === 'debit-plus-credit' ? renderDebitPlusCreditFields() : renderDebitPipeCreditFields()}

      {/* Aggregated Total column (optional, for both formats) */}
      {renderField(
        FIELD_LABELS.AGGREGATED_TOTAL_COLUMN_LABEL,
        FIELD_LABELS.AGGREGATED_TOTAL_COLUMN_PLACEHOLDER,
        config.aggregatedTotalColumn ?? '',
        'aggregatedTotalColumn',
        config.validationErrors?.aggregatedTotalColumn
      )}

      {/* Validation summary */}
      {config.isComplete && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-3">
          <p className="text-sm text-green-800">
            ✓ All required fields completed
          </p>
        </div>
      )}
    </div>
  );
}

/*
 * وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
 */