/*
 * بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ
 * Upload Form Container Component
 * Banking Reconciliation System Frontend
 */

'use client';

import React, { useState } from 'react';
import type { BankStatementFile, CompanyDataFile, ColumnMappingConfiguration } from '../../types/upload';
import type { ReconciliationResult } from '@/types/reconciliation.types';
import { BankUploadZone } from './BankUploadZone';
import { CompanyUploadZone } from './CompanyUploadZone';
import { FormatSelector } from './FormatSelector';
import { ColumnMappingFields } from './ColumnMappingFields';
import { ReconciliationResults } from '@/components/results/ReconciliationResults';
import { reconciliationClient } from '@/lib/api/reconciliationClient';
import { canSubmitForm, preserveCommonFields, updateColumnMappingValidation } from '../../lib/validation';
import { Button } from '@/components/ui/button';

const INITIAL_COLUMN_MAPPING: ColumnMappingConfiguration = {
  formatType: 'debit-plus-credit',
  sheetName: 'Sheet1',
  debitPlusCreditFields: {
    transactionDateColumn: '',
    debitPlusCreditColumn: '',
    transactionDetailsColumn: '',
  },
  isComplete: false,
};

/**
 * Main upload form container component
 * Orchestrates file upload zones and manages form state
 */
export function UploadForm() {
  const [bankStatement, setBankStatement] = useState<BankStatementFile | null>(null);
  const [companyData, setCompanyData] = useState<CompanyDataFile | null>(null);
  const [dragOverZone, setDragOverZone] = useState<'bank' | 'company' | null>(null);
  const [columnMapping, setColumnMapping] = useState<ColumnMappingConfiguration>(INITIAL_COLUMN_MAPPING);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submissionStatus, setSubmissionStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [submissionError, setSubmissionError] = useState<string | undefined>();
  const [reconciliationResult, setReconciliationResult] = useState<ReconciliationResult | null>(null);

  const handleBankFileUpload = (file: BankStatementFile) => {
    setBankStatement(file);
  };

  const handleCompanyFileUpload = (file: CompanyDataFile) => {
    setCompanyData(file);
  };

  const handleBankFileRemove = () => {
    setBankStatement(null);
  };

  const handleCompanyFileRemove = () => {
    setCompanyData(null);
  };

  const handleBankDragEnter = () => {
    setDragOverZone('bank');
  };

  const handleCompanyDragEnter = () => {
    setDragOverZone('company');
  };

  const handleDragLeave = () => {
    setDragOverZone(null);
  };

  const handleFormatChange = (newFormatType: 'debit-plus-credit' | 'debit-pipe-credit') => {
    const updatedConfig = preserveCommonFields(columnMapping, newFormatType);
    setColumnMapping(updatedConfig);
  };

  const handleColumnMappingChange = (updatedConfig: ColumnMappingConfiguration) => {
    const validatedConfig = updateColumnMappingValidation(updatedConfig);
    setColumnMapping(validatedConfig);
  };

  const resetForm = () => {
    setBankStatement(null);
    setCompanyData(null);
    setColumnMapping(INITIAL_COLUMN_MAPPING);
    setSubmissionStatus('idle');
    setSubmissionError(undefined);
    setReconciliationResult(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!canSubmitForm({ bankStatement, companyData, columnMapping })) {
      return;
    }

    if (!bankStatement || !companyData) {
      return;
    }

    setIsSubmitting(true);
    setSubmissionStatus('idle');
    setSubmissionError(undefined);
    setReconciliationResult(null);

    try {
      const sheetName = columnMapping.sheetName.trim() || 'Sheet1';
      let result: ReconciliationResult;

      if (columnMapping.formatType === 'debit-plus-credit' && columnMapping.debitPlusCreditFields) {
        const fields = columnMapping.debitPlusCreditFields;
        result = await reconciliationClient.processReconciliation(
          bankStatement.file,
          companyData.file,
          columnMapping.formatType,
          fields.transactionDateColumn.trim(),
          fields.transactionDetailsColumn.trim(),
          sheetName,
          fields.debitPlusCreditColumn.trim()
        );
      } else if (columnMapping.formatType === 'debit-pipe-credit' && columnMapping.debitPipeCreditFields) {
        const fields = columnMapping.debitPipeCreditFields;
        result = await reconciliationClient.processReconciliation(
          bankStatement.file,
          companyData.file,
          columnMapping.formatType,
          fields.transactionDateColumn.trim(),
          fields.transactionDetailsColumn.trim(),
          sheetName,
          undefined,
          fields.debitColumn.trim(),
          fields.creditColumn.trim()
        );
      } else {
        throw new Error('Invalid column mapping configuration');
      }

      setReconciliationResult(result);
      setSubmissionStatus('success');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (error) {
      setSubmissionStatus('error');
      setSubmissionError(error instanceof Error ? error.message : 'An unexpected error occurred');
    } finally {
      setIsSubmitting(false);
    }
  };

  const canSubmit = canSubmitForm({ bankStatement, companyData, columnMapping });

  if (reconciliationResult) {
    return (
      <div className="w-full max-w-6xl mx-auto p-6">
        <ReconciliationResults result={reconciliationResult} onStartNew={resetForm} />
      </div>
    );
  }

  return (
    <div className="w-full max-w-6xl mx-auto p-6">
      <div className="space-y-6">
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold text-gray-800">
            Bank Reconciliation System
          </h1>
          <p className="text-gray-600">
            Upload your bank statement and company data files to begin reconciliation
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-2">
            <BankUploadZone
              onFileUpload={handleBankFileUpload}
              uploadedFile={bankStatement}
              onFileRemove={handleBankFileRemove}
              dragOverZone={dragOverZone}
              onDragEnter={handleBankDragEnter}
              onDragLeave={handleDragLeave}
            />
          </div>

          <div className="space-y-2">
            <CompanyUploadZone
              onFileUpload={handleCompanyFileUpload}
              uploadedFile={companyData}
              onFileRemove={handleCompanyFileRemove}
              dragOverZone={dragOverZone}
              onDragEnter={handleCompanyDragEnter}
              onDragLeave={handleDragLeave}
            />
          </div>
        </div>

        {bankStatement && companyData && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="text-sm text-blue-800">
              <div className="font-semibold mb-2">Upload Status:</div>
              <div className="space-y-1">
                <div className="flex items-center space-x-2">
                  <span>{bankStatement.isValid ? '✓' : '✗'}</span>
                  <span>Bank Statement: {bankStatement.name}</span>
                  {!bankStatement.isValid && (
                    <span className="text-red-600">
                      ({bankStatement.validationErrors?.join(', ')})
                    </span>
                  )}
                </div>
                <div className="flex items-center space-x-2">
                  <span>{companyData.isValid ? '✓' : '✗'}</span>
                  <span>Company Data: {companyData.name}</span>
                  {!companyData.isValid && (
                    <span className="text-red-600">
                      ({companyData.validationErrors?.join(', ')})
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {bankStatement && companyData && bankStatement.isValid && companyData.isValid && (
          <div className="space-y-6">
            <FormatSelector
              selectedFormat={columnMapping.formatType}
              onFormatChange={handleFormatChange}
              disabled={isSubmitting}
            />

            <ColumnMappingFields
              config={columnMapping}
              onConfigChange={handleColumnMappingChange}
              disabled={isSubmitting}
            />

            <div className="flex justify-center">
              <Button
                type="button"
                size="lg"
                onClick={handleSubmit}
                disabled={!canSubmit || isSubmitting}
                className="min-w-[220px]"
              >
                {isSubmitting ? 'Processing...' : 'Submit for Processing'}
              </Button>
            </div>
          </div>
        )}

        {!canSubmit && (bankStatement || companyData) && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="text-sm text-yellow-800">
              {!bankStatement?.isValid || !companyData?.isValid
                ? 'Please ensure both files are uploaded and valid.'
                : 'Please complete all column mapping fields to submit.'}
            </div>
          </div>
        )}

        {submissionStatus === 'error' && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="text-sm text-red-800">
              <div className="font-semibold mb-1">Submission Failed</div>
              <div>{submissionError || 'An error occurred during submission. Please try again.'}</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/*
 * وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
 */
