/* بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */
/**
 * Advisor API Client (Subh al Baqaya — AI Reconciler Advisor, feature 007)
 * Handles communication with the auth-protected /advisor/* endpoints.
 *
 * Follows the plain-`fetch` singleton pattern of the existing clients
 * (cloudHistoryClient / aiReconciliationClient) with the Bearer access_token
 * from the NextAuth session. The reconcile endpoint streams SSE-style frames:
 * token deltas, then a final typed result frame, or an error frame.
 */

import { signIn } from 'next-auth/react';
import type {
  AdvisorReconcileRequest,
  AdvisorResponse,
  AdvisorStreamFrame,
} from '@/types/advisor.types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export class AdvisorApiError extends Error {
  status: number;
  details?: Record<string, unknown>;

  constructor(message: string, status: number, details?: Record<string, unknown>) {
    super(message);
    this.name = 'AdvisorApiError';
    this.status = status;
    this.details = details;
  }
}

/**
 * Run the Reconciler Agent over the given reconciliation context, consuming
 * the SSE-style stream. `onToken` receives each raw text delta as it arrives;
 * resolves with the final typed AdvisorResponse once the stream completes.
 *
 * @param token - Bearer JWT from the NextAuth session (required; /advisor is NOT auth-exempt).
 * @param request - Full advisor request (discrepancies + balance context + history + question).
 * @param onToken - Optional callback for token-by-token streaming (FR-008c).
 * @param signal - Optional AbortSignal to cancel the fetch mid-stream.
 */
export async function runAdvisorReconcile(
  token: string,
  request: AdvisorReconcileRequest,
  onToken?: (delta: string) => void,
  signal?: AbortSignal,
): Promise<AdvisorResponse> {
  const response = await fetch(`${API_BASE_URL}/advisor/reconcile`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(request),
    signal,
  });

  if (response.status === 401) {
    await signIn('google', { callbackUrl: window.location.href });
    throw new AdvisorApiError('Session expired. Please sign in again.', 401);
  }
  if (!response.ok) {
    throw new AdvisorApiError(`Advisor request failed (${response.status})`, response.status);
  }
  if (!response.body) {
    throw new AdvisorApiError('Advisor response had no body', 0);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  const readFrame = (chunk: string): AdvisorStreamFrame | null => {
    if (!chunk.startsWith('data: ')) return null;
    try {
      return JSON.parse(chunk.slice(6)) as AdvisorStreamFrame;
    } catch {
      return null;
    }
  };

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    // SSE frames are separated by a blank line.
    const frames = buffer.split('\n\n');
    buffer = frames.pop() ?? '';

    for (const frameText of frames) {
      const frame = readFrame(frameText.trim());
      if (!frame) continue;
      if (frame.type === 'token') {
        onToken?.(frame.delta);
      } else if (frame.type === 'result') {
        return frame.data;
      } else if (frame.type === 'error') {
        throw new AdvisorApiError(frame.message, frame.status);
      }
    }
  }

  // If the stream ended without a result frame, surface the raw tail (if any).
  if (buffer.trim()) {
    const frame = readFrame(buffer.trim());
    if (frame?.type === 'error') {
      throw new AdvisorApiError(frame.message, frame.status);
    }
  }
  throw new AdvisorApiError('Advisor stream ended without a result', 0);
}

/**
 * Cancel an in-flight Reconciler Agent request.
 * Uses sendBeacon so it also works from pagehide/beforeunload (reload/close).
 */
export function cancelAdvisorRun(requestId: string): boolean {
  const url = `${API_BASE_URL}/advisor/${encodeURIComponent(requestId)}/cancel`;
  try {
    if (navigator.sendBeacon) {
      return navigator.sendBeacon(url);
    }
    fetch(url, { method: 'POST', keepalive: true }).catch(() => {});
    return true;
  } catch {
    return false;
  }
}

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */