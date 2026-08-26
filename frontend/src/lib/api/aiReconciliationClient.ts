/* بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */
/**
 * API client for the AI reconciliation flow (Istikhraj e Data Ma'a AI)
 * Handles communication with the backend /reconcile-ai endpoint.
 *
 * The client generates the request id up front so an in-flight run can be
 * cancelled (Stop button, page reload) before the response arrives.
 */

import type { ReconciliationResult } from '@/types/reconciliation.types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/** Generate a uuid for the request (crypto.randomUUID when available). */
export function generateRequestId(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID();
  }
  return `req-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

/**
 * AI Reconciliation API Client
 * Uploads PDF + Excel; the AI detects structure automatically (no column mapping).
 */
export const aiReconciliationClient = {
  /**
   * Process bank statement and company records via AI-driven detection
   * @param bankStatement - PDF bank statement file
   * @param companyData - Excel company records file
   * @param historyName - Optional past reconciliation history name to merge (FR-013)
   * @param sheetName - Excel sheet name to read (default "Sheet1")
   * @param requestId - Client-generated id; used to cancel the run mid-flight.
   */
  async processReconciliation(
    bankStatement: File,
    companyData: File,
    historyName?: string,
    sheetName: string = "Sheet1",
    requestId: string = generateRequestId(),
    reconciliationType: "bank" | "vendor" = "bank",
  ): Promise<ReconciliationResult> {
    const formData = new FormData();

    formData.append('bankStatement', bankStatement);
    formData.append('companyData', companyData);
    formData.append('sheetName', sheetName);
    formData.append('requestId', requestId);
    formData.append('reconciliationType', reconciliationType);

    if (historyName) {
      formData.append('historyName', historyName);
    }

    const response = await fetch(`${API_BASE_URL}/reconcile-ai`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      let message = 'We couldn\'t analyze your files. Please try again.';
      let errorCode: string | undefined;
      try {
        const errorData = await response.json();
        if (typeof errorData.detail === 'string') {
          message = errorData.detail;
        } else if (errorData.detail?.message) {
          message = errorData.detail.message;
          errorCode = errorData.detail.error;
        } else if (errorData.message) {
          message = errorData.message;
          errorCode = errorData.error;
        }
      } catch {
        message = `AI reconciliation failed (${response.status})`;
      }
      const err = new Error(message) as Error & { code?: string; status?: number };
      err.code = errorCode;
      err.status = response.status;
      throw err;
    }

    return response.json();
  },

  /**
   * Cancel an in-flight AI reconciliation request.
   * Uses sendBeacon so it also works from pagehide/beforeunload (reload/close).
   */
  cancelProcessing(requestId: string): boolean {
    const url = `${API_BASE_URL}/reconcile-ai/${encodeURIComponent(requestId)}/cancel`;
    try {
      if (navigator.sendBeacon) {
        return navigator.sendBeacon(url);
      }
      // Fallback: fire-and-forget fetch (keepalive so it survives unload).
      fetch(url, { method: 'POST', keepalive: true }).catch(() => {});
      return true;
    } catch {
      return false;
    }
  },
};

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
