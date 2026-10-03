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

/** Sentiment drives the circular gauge: positive increases it, negative decreases, neutral holds. */
export type StageSentiment = 'positive' | 'neutral' | 'negative';

/** A live stage frame emitted by the /reconcile-ai/{id}/events SSE sidecar. */
export interface ReconciliationStageFrame {
  type: 'stage';
  key: string;
  message: string;
  sentiment: StageSentiment;
  emoji: string;
  progress_delta: number;
}

/** Terminal frame emitted when the run finishes/errors/cancels. */
export interface ReconciliationStatusFrame {
  type: 'status';
  state: 'done' | 'error' | 'cancelled';
  message: string;
}

export type ReconciliationProgressFrame =
  | ReconciliationStageFrame
  | ReconciliationStatusFrame;

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
    token?: string,
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

    const headers: Record<string, string> = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}/reconcile-ai`, {
      method: 'POST',
      headers,
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
   * Open the SSE sidecar for an in-flight /reconcile-ai run and stream live
   * progress frames. Resolves when a terminal `done` frame arrives; throws a
   * typed error on an `error`/`cancelled` terminal frame.
   *
   * @param requestId - The client-generated id ALSO sent to /reconcile-ai.
   * @param token - Bearer JWT (the events route is auth-protected).
   * @param onStage - Called for every stage frame as it streams in.
   * @param signal - AbortSignal to close the stream early (page leave/stop).
   */
  async streamProgress(
    requestId: string,
    token: string | undefined,
    onStage: (frame: ReconciliationStageFrame) => void,
    signal?: AbortSignal,
  ): Promise<'done' | 'error' | 'cancelled'> {
    const url = `${API_BASE_URL}/reconcile-ai/${encodeURIComponent(requestId)}/events`;
    const headers: Record<string, string> = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    // The main POST registers the run only after its (large) multipart body has
    // finished uploading, so this tiny sidecar request can reach the server
    // FIRST and get a 404. Blindly treating that race as "done" flips the
    // overlay's done flag before processing even starts, so retry briefly.
    const NOT_FOUND_RETRIES = 12;
    const NOT_FOUND_RETRY_MS = 500;
    let response!: Response;
    for (let attempt = 0; ; attempt++) {
      response = await fetch(url, { method: 'POST', headers, signal });
      if (response.status !== 404 || attempt >= NOT_FOUND_RETRIES) break;
      await new Promise((resolve) => setTimeout(resolve, NOT_FOUND_RETRY_MS));
    }
    if (response.status === 404) {
      // Genuinely no active run for this id (finished too fast / never
      // registered). Treat as done so the UI can proceed.
      return 'done';
    }
    if (!response.ok) {
      throw new Error(`Failed to open progress stream (${response.status})`);
    }
    if (!response.body) {
      throw new Error('Progress stream had no body');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    const readFrame = (chunk: string): ReconciliationProgressFrame | null => {
      if (!chunk.startsWith('data: ')) return null; // ignores ": ping" keep-alives
      try {
        return JSON.parse(chunk.slice(6)) as ReconciliationProgressFrame;
      } catch {
        return null;
      }
    };

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      const frames = buffer.split('\n\n');
      buffer = frames.pop() ?? '';

      for (const frameText of frames) {
        const frame = readFrame(frameText.trim());
        if (!frame) continue;
        if (frame.type === 'stage') {
          onStage(frame);
        } else if (frame.type === 'status') {
          return frame.state;
        }
      }
    }
    // Stream closed without a terminal frame (run finished / server stopped it).
    return 'done';
  },

  /**
   * Cancel an in-flight AI reconciliation request.
   * Uses keepalive fetch so it also works from pagehide/beforeunload
   * (reload/close). The Bearer token is sent because /reconcile-ai is now
   * auth-protected; sendBeacon cannot set headers, so plain fetch is used.
   */
  cancelProcessing(requestId: string, token?: string): boolean {
    const url = `${API_BASE_URL}/reconcile-ai/${encodeURIComponent(requestId)}/cancel`;
    try {
      const headers: Record<string, string> = {};
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      fetch(url, { method: 'POST', keepalive: true, headers }).catch(() => {});
      return true;
    } catch {
      return false;
    }
  },
};

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
