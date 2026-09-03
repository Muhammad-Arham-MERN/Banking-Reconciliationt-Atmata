/*
 * بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ
 * Upload AI Config Component (Istikhraj e Data Ma'a AI)
 * Banking Reconciliation System Frontend
 */

'use client';

import React, { useState, useEffect, useCallback, useRef } from 'react';
import type { BankStatementFile, CompanyDataFile } from '../../types/upload';
import type { ReconciliationResult } from '@/types/reconciliation.types';
import { BankUploadZone } from './BankUploadZone';
import { CompanyUploadZone } from './CompanyUploadZone';
import { ReconciliationResults } from '@/components/results/ReconciliationResults';
import { AIProcessingOverlay } from '@/components/ai/ai-processing-overlay';
import { aiReconciliationClient, generateRequestId } from '@/lib/api/aiReconciliationClient';
import { useSession } from 'next-auth/react';
import { useReconciliationType } from '@/components/providers/reconciliation-type-provider';
import { Button } from '@/components/ui/button';
import { History } from 'lucide-react';
import { PastReconciliationsDrawer } from '@/components/history/PastReconciliationsDrawer';

/**
 * AI-driven upload form (FR-001): uploads PDF + Excel, selects optional past
 * history, and submits WITHOUT any column mapping. The AI detects structure
 * automatically. No column-name fields, no format selector (FR-001/FR-017).
 */
export function UploadAIConfig() {
  const { data: session } = useSession();
  const [bankStatement, setBankStatement] = useState<BankStatementFile | null>(null);
  const [companyData, setCompanyData] = useState<CompanyDataFile | null>(null);
  const [dragOverZone, setDragOverZone] = useState<'bank' | 'company' | null>(null);

  // Past Reconciliations (view / edit / create / load)
  const [pastDrawerOpen, setPastDrawerOpen] = useState(false);
  const [selectedCloudFile, setSelectedCloudFile] = useState<string>('');

  // Excel sheet name (user-provided, FR-001)
  const [sheetName, setSheetName] = useState<string>('Sheet1');

  // Reconciliation type: "bank" (default) or "vendor". Shared via context so
  // the page background and results view react to the same selection.
  const { reconciliationType, setReconciliationType } = useReconciliationType();

  // Submission state
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [errorCode, setErrorCode] = useState<string | undefined>(undefined);
  const [wasStopped, setWasStopped] = useState(false);
  const [partialMessage, setPartialMessage] = useState<string | null>(null);
  const [reconciliationResult, setReconciliationResult] = useState<ReconciliationResult | null>(null);

  // Id of the in-flight AI request; used to cancel on Stop / page reload.
  const activeRequestIdRef = useRef<string | null>(null);

  const handleBankFileUpload = (file: BankStatementFile) => setBankStatement(file);
  const handleCompanyFileUpload = (file: CompanyDataFile) => setCompanyData(file);
  const handleBankFileRemove = () => setBankStatement(null);
  const handleCompanyFileRemove = () => setCompanyData(null);
  const handleBankDragEnter = () => setDragOverZone('bank');
  const handleCompanyDragEnter = () => setDragOverZone('company');
  const handleDragLeave = () => setDragOverZone(null);

  const resetForm = () => {
    setBankStatement(null);
    setCompanyData(null);
    setSelectedCloudFile('');
    setErrorMessage(null);
    setErrorCode(undefined);
    setWasStopped(false);
    setPartialMessage(null);
    setReconciliationResult(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!bankStatement?.isValid || !companyData?.isValid) {
      return;
    }

    // Generate the request id up front so we can cancel the backend run
    // before the response arrives (Stop button, page reload).
    const requestId = generateRequestId();
    activeRequestIdRef.current = requestId;

    setIsSubmitting(true);
    setErrorMessage(null);
    setErrorCode(undefined);
    setWasStopped(false);
    setPartialMessage(null);
    setReconciliationResult(null);

    try {
      const token = (session?.user as { access_token?: string } | undefined)?.access_token;
      const result = await aiReconciliationClient.processReconciliation(
        bankStatement.file,
        companyData.file,
        selectedCloudFile || undefined,
        sheetName.trim() || 'Sheet1',
        requestId,
        reconciliationType,
        token
      );

      if (result.processing_status === 'partial' || result.processing_status === 'error') {
        // Partial success: show successful side's data + clear message (FR-018)
        setPartialMessage(result.message || 'One of the files could not be processed. Please try again.');
        setReconciliationResult(result);
      } else {
        setReconciliationResult(result);
      }
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (error) {
      const err = error as Error & { code?: string; status?: number };
      // If the user cancelled, show a quiet confirmation instead of an error.
      if (err?.code === 'cancelled' || err?.name === 'AbortError' || err?.message?.includes('cancelled')) {
        setWasStopped(true);
        setErrorMessage(null);
        setErrorCode(undefined);
        return;
      }
      // Clear, friendly retry message on failure (FR-009)
      setErrorCode(err?.code);
      setErrorMessage(
        error instanceof Error ? error.message : 'We couldn\'t analyze your files. Please try again.'
      );
    } finally {
      setIsSubmitting(false);
      activeRequestIdRef.current = null;
    }
  };

  // Stop the running backend job (Stop button / page reload).
  const handleStopProcessing = useCallback(() => {
    const requestId = activeRequestIdRef.current;
    if (!requestId) return;
    const token = (session?.user as { access_token?: string } | undefined)?.access_token;
    aiReconciliationClient.cancelProcessing(requestId, token);
    // Hide the overlay immediately; the in-flight fetch will resolve with the
    // cancel response (499) and settle in the catch block.
    setIsSubmitting(false);
    setWasStopped(true);
    setErrorMessage(null);
  }, [session]);

  // If the user reloads or navigates away mid-processing, tell the backend to
  // stop so we don't keep paying for LLM calls (keepalive fetch survives unload).
  useEffect(() => {
    const abortOnUnload = () => {
      const requestId = activeRequestIdRef.current;
      if (requestId) {
        const token = (session?.user as { access_token?: string } | undefined)?.access_token;
        aiReconciliationClient.cancelProcessing(requestId, token);
      }
    };
    window.addEventListener('pagehide', abortOnUnload);
    window.addEventListener('beforeunload', abortOnUnload);
    return () => {
      window.removeEventListener('pagehide', abortOnUnload);
      window.removeEventListener('beforeunload', abortOnUnload);
    };
  }, [session]);

  const canSubmit = !!bankStatement?.isValid && !!companyData?.isValid && !isSubmitting;

  if (reconciliationResult) {
    return (
      <div className="w-full max-w-6xl mx-auto p-6">
        {partialMessage && (
          <div className="mb-4 bg-amber-50 border border-amber-200 rounded-lg p-4 dark:bg-amber-950/40 dark:border-amber-900">
            <div className="text-sm text-amber-800 dark:text-amber-200">
              <div className="font-semibold mb-1">Partial Success</div>
              <div>{partialMessage}</div>
            </div>
          </div>
        )}
        <ReconciliationResults
          result={reconciliationResult}
          onStartNew={resetForm}
          pdfFileName={bankStatement?.name}
          excelFileName={companyData?.name}
        />
      </div>
    );
  }

  return (
    <div className="w-full max-w-6xl mx-auto p-6">
      {isSubmitting && <AIProcessingOverlay onStop={handleStopProcessing} />}
      <div className="space-y-6">
        {/* Past Reconciliations — button opens the right-side drawer */}
        <div className="rounded-xl border border-purple-200 bg-gradient-to-br from-purple-50/70 via-white to-purple-50/30 px-5 py-4 shadow-sm dark:border-purple-900 dark:from-gray-900 dark:via-gray-900 dark:to-gray-900">
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
          <BankUploadZone
            onFileUpload={handleBankFileUpload}
            uploadedFile={bankStatement}
            onFileRemove={handleBankFileRemove}
            dragOverZone={dragOverZone}
            onDragEnter={handleBankDragEnter}
            onDragLeave={handleDragLeave}
          />
          <CompanyUploadZone
            onFileUpload={handleCompanyFileUpload}
            uploadedFile={companyData}
            onFileRemove={handleCompanyFileRemove}
            dragOverZone={dragOverZone}
            onDragEnter={handleCompanyDragEnter}
            onDragLeave={handleDragLeave}
          />
        </div>

        {/* No column mapping fields, no format selector — AI detects structure (FR-001) */}
        {bankStatement && companyData && bankStatement.isValid && companyData.isValid && (
          <div className="space-y-4">
            {/* Reconciliation type: Bank or Vendor */}
            <div className="bg-white/70 border border-gray-200 rounded-lg p-4 max-w-md mx-auto dark:bg-gray-900/70 dark:border-gray-800">
              <label htmlFor="ai-reconciliation-type" className="block text-sm font-medium text-gray-700 mb-2 dark:text-gray-300">
                Reconciliation Type
              </label>
              <div id="ai-reconciliation-type" className="flex gap-3">
                <button
                  type="button"
                  onClick={() => setReconciliationType('bank')}
                  disabled={isSubmitting}
                  className={`flex-1 rounded-md border px-3 py-2 text-sm font-medium transition-colors ${
                    reconciliationType === 'bank'
                      ? 'border-indigo-500 bg-indigo-50 text-indigo-700 dark:border-indigo-400 dark:bg-indigo-950/50 dark:text-indigo-200'
                      : 'border-gray-300 bg-white text-gray-600 hover:border-gray-400 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-300 dark:hover:border-gray-500'
                  }`}
                >
                  Bank
                </button>
                <button
                  type="button"
                  onClick={() => setReconciliationType('vendor')}
                  disabled={isSubmitting}
                  className={`flex-1 rounded-md border px-3 py-2 text-sm font-medium transition-colors ${
                    reconciliationType === 'vendor'
                      ? 'border-amber-500 bg-amber-50 text-amber-700 dark:border-amber-400 dark:bg-amber-950/50 dark:text-amber-200'
                      : 'border-gray-300 bg-white text-gray-600 hover:border-gray-400 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-300 dark:hover:border-gray-500'
                  }`}
                >
                  Vendor
                </button>
              </div>
              <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                {reconciliationType === 'bank'
                  ? 'Bank statement: Credit is +, Debit is - (standard).'
                  : 'Vendor ledger: Debit is +, Credit is - (own convention).'}
              </p>
            </div>
            <div className="bg-white/70 border border-gray-200 rounded-lg p-4 max-w-md mx-auto dark:bg-gray-900/70 dark:border-gray-800">
              <label htmlFor="ai-sheet-name" className="block text-sm font-medium text-gray-700 mb-1 dark:text-gray-300">
                Excel Sheet Name
              </label>
              <input
                id="ai-sheet-name"
                type="text"
                value={sheetName}
                onChange={(e) => setSheetName(e.target.value)}
                disabled={isSubmitting}
                placeholder="Sheet1"
                className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-800 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100"
              />
            </div>
            <div className="flex justify-center">
              <Button type="button" size="lg" onClick={handleSubmit} disabled={!canSubmit} className="min-w-[220px]">
                {isSubmitting ? 'Processing…' : 'Submit for AI Processing'}
              </Button>
            </div>
          </div>
        )}

        {!canSubmit && (bankStatement || companyData) && !isSubmitting && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 dark:bg-yellow-950/40 dark:border-yellow-900">
            <div className="text-sm text-yellow-800 dark:text-yellow-200">
              Please ensure both files are uploaded and valid.
            </div>
          </div>
        )}

        {/* Stopped confirmation (user pressed Stop / cancelled) */}
        {wasStopped && !isSubmitting && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 dark:bg-blue-950/40 dark:border-blue-900">
            <div className="text-sm text-blue-800 dark:text-blue-200">
              <div className="font-semibold mb-1">Processing stopped</div>
              <div>The AI was stopped. You can submit again whenever you&apos;re ready.</div>
              <div className="mt-2">
                <Button variant="outline" size="sm" onClick={() => setWasStopped(false)}>
                  Dismiss
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Friendly retry error (FR-009) */}
        {errorMessage && !isSubmitting && !wasStopped && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 dark:bg-red-950/40 dark:border-red-900">
            <div className="text-sm text-red-800 dark:text-red-200">
              <div className="font-semibold mb-1">
                {errorCode === 'agent_failed'
                  ? 'Agent failed to extract the PDF Structure'
                  : errorCode === 'agent_internal_error'
                    ? 'Agent had internal server error'
                    : 'We couldn&apos;t analyze your files'}
              </div>
              <div>{errorMessage}</div>
              <div className="mt-2">
                <Button variant="outline" size="sm" onClick={() => { setErrorMessage(null); setErrorCode(undefined); }}>
                  Try again
                </Button>
              </div>
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
