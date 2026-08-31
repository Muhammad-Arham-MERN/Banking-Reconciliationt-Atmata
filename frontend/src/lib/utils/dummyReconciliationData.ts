/**
 # بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
 * Dummy Reconciliation Data Generator (frontend /tests endpoint)
 * Feature: 007-ai-reconciler-advisor — test harness for the AI Reconciler Advisor.
 *
 * Produces a realistic ReconciliationResult: 500+ bank/company transactions and
 * 150+ final discrepancies across all four display categories, matching the
 * exact shape the current reconciliation renders (pure convention, no flips):
 *   - UNPRESENTED CHECKS       : Company credit (negative) → displayed negative
 *   - UNCLEARED CHECKS         : Company debit (positive)  → displayed positive
 *   - BANK CREDITED NOT DEBITED: Bank credit (positive)    → displayed positive
 *   - BANK DEBITED NOT CREDITED: Bank debit (negative)     → displayed negative
 *
 * The discrepancy list deliberately embeds the two agent-detectable patterns
 * (broken cheque/pair and reversal) so "Reconcile With Agent" finds them, plus
 * `discrepancy_id` keys so the advisor's Reconcile action resolves exactly.
 */

import type { ReconciliationResult } from '@/types/reconciliation.types';
import type { AdvisorDiscrepancy } from '@/types/advisor.types';

// ============================================================================
// Deterministic pseudo-random generator (seeded → stable dummy data)
// ============================================================================
function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return function () {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const rand = mulberry32(20260827);
const randInt = (min: number, max: number) => Math.floor(rand() * (max - min + 1)) + min;
const pick = <T,>(arr: readonly T[]): T => arr[randInt(0, arr.length - 1)];

// ============================================================================
// Realistic transaction vocabulary
// ============================================================================
const BANK_DETAILS = [
  'INWARD CHEQUE',
  'OUTWARD CHEQUE',
  'FUND TRANSFER THROUGH RTGS FROM MCB',
  'FUND TRANSFER THROUGH RTGS TO SBL',
  'P2P RECEIVING VIA GREAVES',
  'P2P PAYMENT VIA GREAVES',
  'CASH DEPOSIT COUNTER',
  'CASH WITHDRAWAL COUNTER',
  'ATM WITHDRAWAL',
  'SALARY DISBURSEMENT',
  'UTILITY BILL PAYMENT ELECTRICITY',
  'UTILITY BILL PAYMENT GAS',
  'TELECOM PAYMENT',
  'ONLINE BANKING TRANSFER',
  'PROMOTION PAYMENT',
  'RECONCILIATION ADJUSTMENT',
  'CHEQUE BOOK CHARGES',
  'BANK SERVICE CHARGES',
  'PROFIT ON DEPOSIT ACCOUNT',
  'ZAKAT DEDUCTION',
] as const;

const COMPANY_DETAILS = [
  'Cheque #1021 withdrawal',
  'Cheque #1021 partial',
  'Cheque #1021 full amount',
  'Payment reversal - invoice 431',
  'Reversal of payment 431',
  'Invoice payment to vendor',
  'Advance salary to employee',
  'Office rent payment',
  'Utility bills settlement',
  'Client payment received',
  'Supplier settlement',
  'Miscellaneous expense',
  'Petty cash replenishment',
  'Loan installment payment',
  'Insurance premium payment',
  'Maintenance charges',
  'Freight and shipping charges',
  'Custom duty payment',
  'Audit fee payment',
  'Tax payment advance',
] as const;

// Realistic supplier / vendor names for the details text
const COUNTERPARTIES = [
  'Suzuki Azim Motors',
  'MCB Bank Ltd',
  'SBL Bank',
  'Greaves Pakistan',
  'K-Electric',
  'SNGPL',
  'Jazz Telecom',
  'Habib Metropolitan',
  'Punjab Supply Co',
  'Al-Falah Traders',
  'National Foods',
  'Lucky Cement',
  'Engro Corporation',
  'Fauji Fertilizer',
  'Gul Ahmed Textiles',
  'Nestle Pakistan',
  'Unilever Pakistan',
  'Atlas Honda',
  'Pak Suzuki',
  'Millat Tractors',
] as const;

// ============================================================================
// Date helpers (April–July 2026 range, realistic for a bank statement)
// ============================================================================
const DATE_START = Date.UTC(2026, 3, 1); // 2026-04-01
const DATE_END = Date.UTC(2026, 6, 31); // 2026-07-31
const DAY_MS = 86400000;

function randomDateISO(): string {
  const ts = randInt(DATE_START, DATE_END);
  return new Date(ts).toISOString().slice(0, 10);
}

function addDaysISO(base: string, days: number): string {
  const d = new Date(base + 'T00:00:00Z');
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
}

// ============================================================================
// Amount generators
// ============================================================================
/** Random signed transaction amount in whole rupees (negative = debit). */
function randomAmount(): number {
  const sign = rand() < 0.5 ? -1 : 1;
  const magnitude = randInt(1, 200) * 1000 + randInt(0, 9) * 100 + randInt(1, 99);
  return sign * magnitude;
}

/** Round amount to whole rupees (matches the engine's whole-rupee rounding). */
function roundAmount(value: number): number {
  return Math.round(value);
}

// ============================================================================
// Discrepancy category helpers
// ============================================================================
type DiscrepancyKind =
  | 'unpresented' // Company negative
  | 'uncleared' // Company positive
  | 'bankCredited' // Bank positive (displayed negative)
  | 'bankDebited'; // Bank negative (displayed positive)

interface DiscrepancyItem {
  'Transaction_date': string;
  'Transaction Detail': string;
  'Debit/Credit': number;
  FROM: 'Bank' | 'Company';
  from_past?: boolean;
  discrepancy_id: string;
}
export function generateDummyReconciliation(): ReconciliationResult {
  // ---- Bank transactions (300) ----
  const bank_transactions: Array<{
    'Transaction_date': string;
    'Transaction Detail': string;
    'Debit/Credit': number;
  }> = [];
  for (let i = 0; i < 300; i++) {
    const amount = randomAmount();
    // Bias toward bank debits (money out) — realistic for a statement.
    bank_transactions.push({
      'Transaction_date': randomDateISO(),
      'Transaction Detail': pick(BANK_DETAILS),
      'Debit/Credit': amount,
    });
  }

  // ---- Company transactions (300) ----
  const company_transactions: Array<{
    'Transaction_date': string;
    'Transaction Detail': string;
    'Debit/Credit': number;
  }> = [];
  for (let i = 0; i < 300; i++) {
    const amount = randomAmount();
    company_transactions.push({
      'Transaction_date': randomDateISO(),
      'Transaction Detail': pick(COMPANY_DETAILS),
      'Debit/Credit': amount,
    });
  }

  // ---- Final discrepancies (150) ----
  // Deliberately structured across all four categories. Two agent-detectable
  // patterns are embedded at known positions:
  //   - BROKEN_CHEQUE: Bank +79,000 and +100,000 vs Company -179,000
  //   - REVERSAL:      Company -45,000 (Jul 19) and +45,000 (Jul 24)
  const discrepancies: DiscrepancyItem[] = [];

  // 1) UNPRESENTED CHECKS — Company negative (44 items)
  for (let i = 0; i < 44; i++) {
    discrepancies.push({
      'Transaction_date': randomDateISO(),
      'Transaction Detail': `${pick(COMPANY_DETAILS)} - cheque issued`,
      'Debit/Credit': -Math.abs(randomAmount()),
      FROM: 'Company',
      discrepancy_id: `Company:${i + 1}`,
    });
  }

  // 2) UNCLEARED CHECKS — Company positive (40 items)
  for (let i = 0; i < 40; i++) {
    discrepancies.push({
      'Transaction_date': randomDateISO(),
      'Transaction Detail': `${pick(COMPANY_DETAILS)} - receipt`,
      'Debit/Credit': Math.abs(randomAmount()),
      FROM: 'Company',
      discrepancy_id: `Company:${44 + i + 1}`,
    });
  }

  // 3) BANK CREDITED BUT NOT DEBITED — Bank positive (credit), displayed positive (34 items)
  for (let i = 0; i < 34; i++) {
    discrepancies.push({
      'Transaction_date': randomDateISO(),
      'Transaction Detail': pick(BANK_DETAILS),
      'Debit/Credit': Math.abs(randomAmount()),
      FROM: 'Bank',
      discrepancy_id: `Bank:${i + 1}`,
    });
  }

  // 4) BANK DEBITED BUT NOT CREDITED — Bank negative (debit), displayed negative (32 items)
  for (let i = 0; i < 32; i++) {
    discrepancies.push({
      'Transaction_date': randomDateISO(),
      'Transaction Detail': pick(BANK_DETAILS),
      'Debit/Credit': -Math.abs(randomAmount()),
      FROM: 'Bank',
      discrepancy_id: `Bank:${34 + i + 1}`,
    });
  }

  // ---- Embed the two agent-detectable patterns (overwrite first slots) ----
  // Broken cheque: Bank +79,000 + +100,000 vs Company -179,000.
  // Replaces two Bank-positive rows (bankCredited) and one Company-negative row.
  discrepancies[0] = {
    'Transaction_date': '2026-07-10',
    'Transaction Detail': 'Cheque #1021 withdrawal',
    'Debit/Credit': 79000,
    FROM: 'Bank',
    discrepancy_id: 'Bank:1',
  };
  discrepancies[1] = {
    'Transaction_date': '2026-07-12',
    'Transaction Detail': 'Cheque #1021 partial',
    'Debit/Credit': 100000,
    FROM: 'Bank',
    discrepancy_id: 'Bank:2',
  };
  // Company-side whole (first unpresented slot = Company:1).
  discrepancies[44] = {
    'Transaction_date': '2026-07-11',
    'Transaction Detail': 'Cheque #1021 full amount',
    'Debit/Credit': -179000,
    FROM: 'Company',
    discrepancy_id: 'Company:1',
  };

  // Reversal: Company -45,000 (Jul 19) and +45,000 (Jul 24), "reversal" language.
  // Replaces two Company rows (one unpresented, one uncleared).
  discrepancies[45] = {
    'Transaction_date': '2026-07-19',
    'Transaction Detail': 'Payment reversal - invoice 431',
    'Debit/Credit': -45000,
    FROM: 'Company',
    discrepancy_id: 'Company:2',
  };
  discrepancies[86] = {
    'Transaction_date': '2026-07-24',
    'Transaction Detail': 'Reversal of payment 431',
    'Debit/Credit': 45000,
    FROM: 'Company',
    discrepancy_id: 'Company:3',
  };

  // ---- Re-key discrepancy_ids sequentially per source ----
  // Mirrors the backend assignment (Bank items first, then Company items, in
  // final array order): guarantees unique, stable keys after the pattern
  // overwrites above.
  const bankCounters: Record<string, number> = {};
  for (const d of discrepancies) {
    bankCounters[d.FROM] = (bankCounters[d.FROM] ?? 0) + 1;
    d.discrepancy_id = `${d.FROM}:${bankCounters[d.FROM]}`;
  }

  // ---- Compute the cumulative Bank/Company balance context (FR-002b) ----
  let bankRunning = 0;
  let companyRunning = 0;
  const points = discrepancies.map((d, index) => {
    if (d.FROM === 'Company') {
      companyRunning += d['Debit/Credit'];
    } else {
      bankRunning += d['Debit/Credit'];
    }
    return {
      index: index + 1,
      discrepancy_id: d.discrepancy_id,
      bank_running: roundAmount(bankRunning),
      company_running: roundAmount(companyRunning),
      net: roundAmount(bankRunning + companyRunning),
    };
  });

  const bankOnly = discrepancies.filter((d) => d.FROM === 'Bank').length;
  const companyOnly = discrepancies.filter((d) => d.FROM === 'Company').length;
  const totalDiscrepancies = discrepancies.length;

  // Realistic net totals for the verification panel.
  const bankNetTotal = {
    value: bankOnly > 0 ? Math.abs(discrepancies.filter((d) => d.FROM === 'Bank').reduce((s, d) => s + d['Debit/Credit'], 0)) : null,
    status: 'found' as const,
  };
  const companyNetTotal = {
    value: companyOnly > 0 ? Math.abs(discrepancies.filter((d) => d.FROM === 'Company').reduce((s, d) => s + d['Debit/Credit'], 0)) : null,
    status: 'found' as const,
  };

  const result: ReconciliationResult = {
    request_id: 'dummy-test-reconciliation-001',
    processing_status: 'completed',
    processing_timestamp: new Date().toISOString(),
    summary: {
      total_bank_transactions: bank_transactions.length,
      total_company_transactions: company_transactions.length,
      total_discrepancies: totalDiscrepancies,
      bank_only_discrepancies: bankOnly,
      company_only_discrepancies: companyOnly,
      opposite_pairs_removed: 0,
      pair_mate_pairs_removed: 0,
      processing_duration_ms: 1234,
      pdf_processing_time_ms: 900,
      excel_processing_time_ms: 334,
      concurrent_processing: true,
    },
    results: {
      bank_statement: bank_transactions,
      company_records: company_transactions,
      // The displayed discrepancy list — exact same shape the real
      // reconciliation emits (spaced keys + discrepancy_id + from_past).
      discrepancies: discrepancies.map((d) => ({
        'Transaction_date': d['Transaction_date'],
        'Transaction Detail': d['Transaction Detail'],
        'Debit/Credit': d['Debit/Credit'],
        FROM: d.FROM,
        from_past: d.from_past,
        discrepancy_id: d.discrepancy_id,
      })),
    },
    bank_net_total: bankNetTotal,
    company_net_total: companyNetTotal,
    errors: [],
    message: `✅ Dummy reconciliation complete - Found ${totalDiscrepancies} discrepancies`,
  };

  return result;
}

// ============================================================================
// Typed helper for the advisor client payloads (maps to AdvisorDiscrepancy)
// ============================================================================
export function toAdvisorDiscrepancies(
  result: ReconciliationResult
): AdvisorDiscrepancy[] {
  return (result.results.discrepancies ?? []).map((d) => ({
    discrepancy_id: d.discrepancy_id ?? '',
    Transaction_date: d['Transaction_date'],
    Transaction_Detail: d['Transaction Detail'],
    'Debit/Credit': d['Debit/Credit'],
    FROM: d.FROM,
    from_past: d.from_past,
  }));
}

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
