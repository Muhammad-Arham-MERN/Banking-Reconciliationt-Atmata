/*
 * بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ
 * Format Selector Component
 * Banking Reconciliation System Frontend
 */

'use client';

import React from 'react';
import { FORMAT_OPTIONS, FIELD_LABELS } from '../../lib/constants';
import type { FormatType } from '../../types/upload';

interface FormatSelectorProps {
  selectedFormat: FormatType;
  onFormatChange: (format: FormatType) => void;
  disabled?: boolean;
}

/**
 * Format selector dropdown component
 * Allows users to choose between debit+credit and debit|credit formats
 */
export function FormatSelector({
  selectedFormat,
  onFormatChange,
  disabled = false,
}: FormatSelectorProps) {
  return (
    <div className="space-y-2">
      <label
        htmlFor="format-selector"
        className="block text-sm font-medium text-gray-700 dark:text-gray-300"
      >
        {FIELD_LABELS.FORMAT_SELECTOR_LABEL}
      </label>

      <select
        id="format-selector"
        value={selectedFormat}
        onChange={(e) => onFormatChange(e.target.value as FormatType)}
        disabled={disabled}
        className={`
          w-full px-4 py-2 rounded-lg border-2 border-gray-300 dark:border-gray-700
          bg-white text-gray-800 font-medium dark:bg-gray-900 dark:text-gray-100
          focus:border-[#FF8A65] focus:ring-2 focus:ring-[#FF8A65] focus:ring-opacity-50
          transition-all duration-200
          disabled:opacity-50 disabled:cursor-not-allowed
        `}
      >
        <option value="" disabled>
          {FIELD_LABELS.FORMAT_SELECTOR_PLACEHOLDER}
        </option>

        {FORMAT_OPTIONS.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>

      {/* Format description */}
      {selectedFormat && (
        <div className="mt-2 p-3 bg-blue-50 border border-blue-200 rounded-lg dark:bg-blue-950/50 dark:border-blue-900">
          <p className="text-sm text-blue-800 dark:text-blue-200">
            {FORMAT_OPTIONS.find((opt) => opt.value === selectedFormat)?.description}
          </p>
          <p className="text-xs text-blue-600 mt-1 dark:text-blue-300">
            This format requires {selectedFormat === 'debit-plus-credit' ? '3' : '4'} column mappings.
          </p>
        </div>
      )}
    </div>
  );
}

/*
 * وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
 */