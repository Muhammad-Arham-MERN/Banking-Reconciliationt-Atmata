/**
 * API client for reconciliation results
 * Handles communication with backend reconciliation endpoints
 */

import { ReconciliationResult } from '@/types/reconciliation.types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Reconciliation API Client
 * Provides methods to interact with reconciliation endpoints
 */
export const reconciliationClient = {
  /**
   * Process bank statement and company records for reconciliation
   * @param bankStatement - PDF bank statement file
   * @param companyData - Excel company records file
   * @param formatType - Format type for Excel data
   * @param transactionDateColumn - Date column name in Excel
   * @param transactionDetailsColumn - Details column name in Excel
   * @param sheetName - Excel sheet name (default: "Sheet1")
   * @param debitPlusCreditColumn - Combined debit/credit column (for debit-plus-credit format)
   * @param debitColumn - Debit column (for debit-pipe-credit format)
   * @param creditColumn - Credit column (for debit-pipe-credit format)
   */
  async processReconciliation(
    bankStatement: File,
    companyData: File,
    formatType: string,
    transactionDateColumn: string,
    transactionDetailsColumn: string,
    sheetName: string = "Sheet1",
    debitPlusCreditColumn?: string,
    debitColumn?: string,
    creditColumn?: string,
    aggregatedTotalColumn?: string
  ): Promise<ReconciliationResult> {
    const formData = new FormData();

    formData.append('bankStatement', bankStatement);
    formData.append('companyData', companyData);
    formData.append('formatType', formatType);
    formData.append('transactionDateColumn', transactionDateColumn);
    formData.append('transactionDetailsColumn', transactionDetailsColumn);
    formData.append('sheetName', sheetName);

    if (debitPlusCreditColumn) {
      formData.append('debitPlusCreditColumn', debitPlusCreditColumn);
    }

    if (debitColumn) {
      formData.append('debitColumn', debitColumn);
    }

    if (creditColumn) {
      formData.append('creditColumn', creditColumn);
    }

    if (aggregatedTotalColumn) {
      formData.append('aggregatedTotalColumn', aggregatedTotalColumn);
    }

    const response = await fetch(`${API_BASE_URL}/karwai`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      let message = 'Reconciliation processing failed';
      try {
        const errorData = await response.json();
        if (typeof errorData.detail === 'string') {
          message = errorData.detail;
        } else if (errorData.detail?.message) {
          message = errorData.detail.message;
        } else if (errorData.message) {
          message = errorData.message;
        }
      } catch {
        message = `Reconciliation failed (${response.status})`;
      }
      throw new Error(message);
    }

    return response.json();
  },

  /**
   * Check API health status
   */
  async checkHealth(): Promise<{ status: string; service: string; version: string; timestamp: string }> {
    const response = await fetch(`${API_BASE_URL}/health`);

    if (!response.ok) {
      throw new Error('Health check failed');
    }

    return response.json();
  }
};

// وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِين
