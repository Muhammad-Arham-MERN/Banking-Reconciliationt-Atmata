/*
 * بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ
 * Upload Form Container Component
 * Banking Reconciliation System Frontend
 */

'use client';

import React, { useState } from 'react';
import { useSession } from 'next-auth/react';
import type { BankStatementFile, CompanyDataFile, ColumnMappingConfiguration } from '../../types/upload';
import type { ReconciliationResult, DiscrepancyTransaction } from '@/types/reconciliation.types';
import type { MergeHistoryEntry } from '@/types/cloud-history.types';
import { BankUploadZone } from './BankUploadZone';
import { CompanyUploadZone } from './CompanyUploadZone';
import { FormatSelector } from './FormatSelector';
import { ColumnMappingFields } from './ColumnMappingFields';
import { ReconciliationResults } from '@/components/results/ReconciliationResults';
import { reconciliationClient } from '@/lib/api/reconciliationClient';
import { cloudHistoryClient } from '@/lib/api/cloudHistoryClient';
import { canSubmitForm, preserveCommonFields, updateColumnMappingValidation } from '../../lib/validation';
import { Button } from '@/components/ui/button';
import { History } from 'lucide-react';
import { ReconciliationTypeProvider } from '@/components/providers/reconciliation-type-provider';
import { PastReconciliationsDrawer } from '@/components/history/PastReconciliationsDrawer';

const INITIAL_COLUMN_MAPPING: ColumnMappingConfiguration = {
  formatType: 'debit-plus-credit',
  sheetName: 'Sheet1',
  aggregatedTotalColumn: 'Cumulative Balance (LC)',
  debitPlusCreditFields: {
    transactionDateColumn: 'Posting Date',
    debitPlusCreditColumn: 'Deb./Cred. (LC)',
    transactionDetailsColumn: 'Transaction Details',
  },
  isComplete: true,
};

/**
 * Main upload form container component
 * Orchestrates file upload zones and manages form state
 */
export function UploadForm() {
  const { data: session } = useSession();
  const [bankStatement, setBankStatement] = useState<BankStatementFile | null>(null);
  const [companyData, setCompanyData] = useState<CompanyDataFile | null>(null);
  const [dragOverZone, setDragOverZone] = useState<'bank' | 'company' | null>(null);
  const [columnMapping, setColumnMapping] = useState<ColumnMappingConfiguration>(INITIAL_COLUMN_MAPPING);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submissionStatus, setSubmissionStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [submissionError, setSubmissionError] = useState<string | undefined>();
  const [reconciliationResult, setReconciliationResult] = useState<ReconciliationResult | null>(null);

  // Past Reconciliations (view / edit / create / load)
  const [pastDrawerOpen, setPastDrawerOpen] = useState(false);
  const [selectedCloudFile, setSelectedCloudFile] = useState<string>('');

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

      const aggregatedTotalColumn = columnMapping.aggregatedTotalColumn?.trim() || undefined;
      const token = (session?.user as { access_token?: string } | undefined)?.access_token;

      if (columnMapping.formatType === 'debit-plus-credit' && columnMapping.debitPlusCreditFields) {
        const fields = columnMapping.debitPlusCreditFields;
        result = await reconciliationClient.processReconciliation(
          bankStatement.file,
          companyData.file,
          columnMapping.formatType,
          fields.transactionDateColumn.trim(),
          fields.transactionDetailsColumn.trim(),
          sheetName,
          fields.debitPlusCreditColumn.trim(),
          undefined,
          undefined,
          aggregatedTotalColumn,
          token
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
          fields.creditColumn.trim(),
          aggregatedTotalColumn,
          token
        );
      } else {
        throw new Error('Invalid column mapping configuration');
      }

      // Merge past discrepancies if a history file is selected
      if (selectedCloudFile && token) {
        try {
          const pastData = await cloudHistoryClient.loadByName(token, selectedCloudFile);
          const currentDiscrepancies = result.results.discrepancies || [];
          const mergedDiscrepancies = mergeDiscrepancies(currentDiscrepancies, pastData.discrepancies);
          result.results.discrepancies = mergedDiscrepancies;
        } catch (err) {
          console.error('Failed to load past discrepancies:', err);
        }
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

  // Merge past discrepancies with current ones, suppressing exact duplicates (same details + same date)
  function mergeDiscrepancies(
    current: DiscrepancyTransaction[],
    past: MergeHistoryEntry[]
  ): DiscrepancyTransaction[] {
    const currentKeys = new Set(
      current.map(d => `${d['Transaction Detail'] ?? ''}|${d['Transaction_date'] ?? ''}`)
    );
    const toAdd = past.filter(p => {
      const key = `${p.transaction_details}|${p.transaction_date}`;
      return !currentKeys.has(key);
    });
    const mapped: DiscrepancyTransaction[] = toAdd.map(p => ({
      'Transaction_date': p.transaction_date,
      'Transaction Detail': p.transaction_details,
      'Debit/Credit': p.debit_credit_amount,
      'FROM': p.category && p.category.includes('Bank') ? 'Bank' : 'Company',
      from_past: true,
    }));
    // Sort combined list by date
    const combined = [...current, ...mapped];
    combined.sort((a, b) => {
      const da = a['Transaction_date'] ?? '';
      const db = b['Transaction_date'] ?? '';
      return da.localeCompare(db);
    });
    return combined;
  }

  if (reconciliationResult) {
    return (
      <ReconciliationTypeProvider>
        <div className="w-full max-w-6xl mx-auto p-6">
          <ReconciliationResults
            result={reconciliationResult}
            onStartNew={resetForm}
            pdfFileName={bankStatement?.name}
            excelFileName={companyData?.name}
          />
        </div>
      </ReconciliationTypeProvider>
    );
  }

  return (
    <div className="w-full max-w-6xl mx-auto p-6">
      <div className="space-y-6">
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold text-gray-800 dark:text-gray-100">
            Bank Reconciliation System
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Upload your bank statement and company data files to begin reconciliation
          </p>
        </div>

        {/* Past Reconciliations — button opens the right-side drawer */}
        <div className="rounded-xl border border-purple-200 bg-gradient-to-br from-purple-50/70 via-white to-purple-50/30 px-5 py-4 shadow-sm transition-all duration-200 hover:shadow-md hover:border-purple-300 dark:border-purple-900 dark:from-gray-900 dark:via-gray-900 dark:to-gray-900 dark:hover:border-purple-700">
          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex items-center gap-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-purple-100 text-purple-600 dark:bg-purple-900/50 dark:text-purple-300">
                <svg width="14" height="14" viewBox="0 0 15 15" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M7.5 1.5C4.5 1.5 2 4 2 7.5C2 11 4.5 13.5 7.5 13.5C10.5 13.5 13 11 13 7.5C13 4 10.5 1.5 7.5 1.5Z" stroke="currentColor" strokeWidth="1.2"/>
                  <path d="M7.5 5V8M7.5 10V9.5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
                </svg>
              </div>
              <label className="text-sm font-semibold text-purple-900 whitespace-nowrap dark:text-purple-200">
                Past Reconciliations
              </label>
            </div>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setPastDrawerOpen(true)}
              title="View, edit, create or load past reconciliations"
              className="gap-1.5"
            >
              <History className="size-4" />
              {selectedCloudFile ? `Loaded: ${selectedCloudFile}` : 'Open Past Reconciliations'}
            </Button>
            {selectedCloudFile && (
              <div className="flex items-center gap-1.5 rounded-full bg-purple-100/80 px-3 py-1 text-xs font-medium text-purple-700 dark:bg-purple-900/50 dark:text-purple-300">
                <svg width="10" height="10" viewBox="0 0 15 15" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M7.5 1.5C4.5 1.5 2 4 2 7.5C2 11 4.5 13.5 7.5 13.5C10.5 13.5 13 11 13 7.5C13 4 10.5 1.5 7.5 1.5Z" stroke="currentColor" strokeWidth="1.2"/>
                  <path d="M7.5 5V8M7.5 10V9.5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
                </svg>
                Past discrepancies will merge into results
              </div>
            )}
          </div>
        </div>

        <PastReconciliationsDrawer
          open={pastDrawerOpen}
          onOpenChange={setPastDrawerOpen}
          onLoadFile={setSelectedCloudFile}
        />

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
