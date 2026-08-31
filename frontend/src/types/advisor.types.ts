/**
 # بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
 * TypeScript types for the AI Reconciler Advisor (Subh al Baqaya, feature 007)
 */

export type AdvisorSource = 'Bank' | 'Company';

export interface AdvisorDiscrepancy {
  discrepancy_id: string;
  Transaction_date: string;
  /** Safe underscore key (wire format) — never the fragile spaced form. */
  Transaction_Detail: string;
  'Debit/Credit': number;
  FROM: AdvisorSource;
  from_past?: boolean;
}

export interface BalancePoint {
  index: number;
  discrepancy_id: string;
  bank_running: number;
  company_running: number;
  net: number;
}

export interface BalanceContext {
  points: BalancePoint[];
  bank_balance: number;
  company_balance: number;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface AdvisorSuggestionItem {
  discrepancy_id: string;
  date: string;
  details: string;
  debit_credit: number;
  source: AdvisorSource;
}

/** Canonical suggestion types; the agent may return other human-readable
 *  type names when the user explicitly asks in chat for additional
 *  reconcilables. */
export type AdvisorSuggestionType = 'BROKEN_CHEQUE' | 'REVERSAL' | (string & {});

export interface AdvisorSuggestion {
  keys: string[];
  type: AdvisorSuggestionType;
  company_items: AdvisorSuggestionItem[];
  bank_items: AdvisorSuggestionItem[];
  reason: string;
}

export interface AdvisorResponse {
  suggestions: AdvisorSuggestion[];
  chat_message: string;
}

export interface AdvisorReconcileRequest {
  request_id: string;
  discrepancies: AdvisorDiscrepancy[];
  context: BalanceContext;
  history: ChatMessage[];
  question?: string | null;
}

/** One frame of the SSE-style stream from POST /advisor/reconcile */
export type AdvisorStreamFrame =
  | { type: 'token'; delta: string }
  | { type: 'result'; data: AdvisorResponse }
  | {
      type: 'error';
      status: number;
      error: string;
      message: string;
    };

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
