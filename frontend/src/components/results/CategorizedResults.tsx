/**
 # بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
 * Categorized Results Component for Reconciliation Frontend Enhancements
 * Feature: 001-reconciliation-frontend-features
 *
 * This component displays unreconciled transactions automatically categorized into
 * four accounting-specific sections based on transaction source and value polarity.
 */

'use client';

import { useMemo } from 'react';
import { DiscrepancyTransaction, NetTotalValue } from '@/types/reconciliation.types';
import { ManualReconciliation } from '@/components/results/ManualReconciliation';
import {
  TransactionCategory,
  CategorizedTransaction
} from '@/types/categorization.types';
import {
  categorizeTransaction,
  generateItemId,
  getDisplayAmount,
  formatAmount
} from '@/lib/utils/categorizationUtils';
import { CheckCircle2, XCircle, AlertTriangle } from 'lucide-react';

interface CategorizedResultsProps {
  discrepancies: DiscrepancyTransaction[];
  bankNetTotal?: NetTotalValue;
  companyNetTotal?: NetTotalValue;
  selectedItems?: Set<string>;
  onToggleSelection?: (itemId: string) => void;
  onReconcile?: (selectedItemIds: Set<string>) => void;
}

/**
 * وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
 * Main categorization results component
 */
export function CategorizedResults({ discrepancies, bankNetTotal, companyNetTotal, selectedItems, onToggleSelection, onReconcile }: CategorizedResultsProps) {
  // Memoized categorization of transactions
  const categorizedData = useMemo(() => {
    return discrepancies.map((d, index) => {
      const category = categorizeTransaction(d.FROM, d['Debit/Credit']);
      const itemId = generateItemId(d['Transaction_date'], d.FROM, d['Debit/Credit'], index);
      const displayAmount = getDisplayAmount(d.FROM, d['Debit/Credit'], category);

      return {
        ...d,
        category,
        itemId,
        displayAmount,
        displayValue: formatAmount(displayAmount)
      };
    });
  }, [discrepancies]);

  // Group transactions by category
  const categories = useMemo(() => {
    const grouped: { [key in TransactionCategory]: CategorizedTransaction[] } = {
      [TransactionCategory.UNPRESENTED_CHECKS]: [],
      [TransactionCategory.UNCLEARED_CHECKS]: [],
      [TransactionCategory.BANK_DEBITED_NOT_CREDITED]: [],
      [TransactionCategory.BANK_CREDITED_NOT_DEBITED]: []
    };

    categorizedData.forEach(transaction => {
      grouped[transaction.category].push(transaction);
    });

    return grouped;
  }, [categorizedData]);

  const categoryCount = {
    [TransactionCategory.UNPRESENTED_CHECKS]: categories[TransactionCategory.UNPRESENTED_CHECKS].length,
    [TransactionCategory.UNCLEARED_CHECKS]: categories[TransactionCategory.UNCLEARED_CHECKS].length,
    [TransactionCategory.BANK_DEBITED_NOT_CREDITED]: categories[TransactionCategory.BANK_DEBITED_NOT_CREDITED].length,
    [TransactionCategory.BANK_CREDITED_NOT_DEBITED]: categories[TransactionCategory.BANK_CREDITED_NOT_DEBITED].length
  };

  const categorySubtotals = useMemo(() => {
    const subtotals: Record<string, { total: number; count: number }> = {};
    for (const [category, txs] of Object.entries(categories)) {
      const total = txs.reduce((sum, t) => sum + t.displayAmount, 0);
      subtotals[category] = { total, count: txs.length };
    }
    return subtotals;
  }, [categories]);

  const totalNet = useMemo(() => {
    return categorizedData.reduce((sum, t) => sum + t.displayAmount, 0);
  }, [categorizedData]);

  // Compute adjusted company balance and reconciliation verdict
  const reconciliationVerdict = useMemo(() => {
    const bankClosing = bankNetTotal?.status === 'found' ? bankNetTotal.value ?? null : null;
    const companyClosing = companyNetTotal?.status === 'found' ? companyNetTotal.value ?? null : null;

    // Adjusted Company Book Balance = Bank Closing Balance + Net Total Across All Categories
    const adjustedCompany = bankClosing !== null ? bankClosing + totalNet : null;

    let isBalanced: boolean | null = null;
    let difference: number | null = null;

    if (adjustedCompany !== null && companyClosing !== null) {
      difference = Math.abs(adjustedCompany - companyClosing);
      isBalanced = difference < 0.001;
    }

    return { bankClosing, companyClosing, adjustedCompany, isBalanced, difference };
  }, [bankNetTotal, companyNetTotal, totalNet]);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <p className="text-sm text-muted-foreground pt-2">
          Found <span className="font-semibold text-foreground">{discrepancies.length}</span> transactions
          <span className="text-muted-foreground"> across 4 categories</span>
        </p>

        {/* Peach-red Bank Closing Balance section (right side) */}
        {reconciliationVerdict.bankClosing !== null && (
          <div className="bg-[#FFF0E6] border border-[#E8A78B] rounded-lg px-5 py-3 shadow-sm min-w-[180px]">
            <p className="text-xs font-semibold uppercase tracking-wide text-[#A0522D]">
              Bank Closing Balance
            </p>
            <p className="text-2xl font-bold text-[#8B4513] font-mono">
              {formatAmount(reconciliationVerdict.bankClosing)}
            </p>
          </div>
        )}
      </div>

      <CategorySection
        title="UNPRESENTED CHECKS"
        transactions={categories[TransactionCategory.UNPRESENTED_CHECKS]}
        count={categoryCount[TransactionCategory.UNPRESENTED_CHECKS]}
        selectedItems={selectedItems}
        onToggleSelection={onToggleSelection}
      />

      <CategorySection
        title="UNCLEARED CHECKS"
        transactions={categories[TransactionCategory.UNCLEARED_CHECKS]}
        count={categoryCount[TransactionCategory.UNCLEARED_CHECKS]}
        selectedItems={selectedItems}
        onToggleSelection={onToggleSelection}
      />

      <CategorySection
        title={TransactionCategory.BANK_CREDITED_NOT_DEBITED}
        transactions={categories[TransactionCategory.BANK_CREDITED_NOT_DEBITED]}
        count={categoryCount[TransactionCategory.BANK_CREDITED_NOT_DEBITED]}
        selectedItems={selectedItems}
        onToggleSelection={onToggleSelection}
      />

      <CategorySection
        title={TransactionCategory.BANK_DEBITED_NOT_CREDITED}
        transactions={categories[TransactionCategory.BANK_DEBITED_NOT_CREDITED]}
        count={categoryCount[TransactionCategory.BANK_DEBITED_NOT_CREDITED]}
        selectedItems={selectedItems}
        onToggleSelection={onToggleSelection}
      />

      {/* Net Total Summary */}
      <div className="rounded-lg border bg-muted/30 p-4">
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-semibold">Net Total Across All Categories</h4>
          <span className={`text-lg font-bold font-mono ${
            totalNet >= 0 ? 'text-green-600' : 'text-red-600'
          }`}>
            {formatAmount(totalNet)}
          </span>
        </div>
        <div className="mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
          {Object.entries(categorySubtotals).map(([category, { total, count }]) => (
            count > 0 && (
              <div key={category} className="rounded border bg-background px-3 py-2 text-xs">
                <p className="font-medium text-muted-foreground truncate" title={category}>
                  {category.length > 30 ? category.slice(0, 30) + '…' : category}
                </p>
                <p className={`mt-0.5 font-mono font-semibold ${
                  total >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {total.toLocaleString('en-US', {
                    style: 'currency',
                    currency: 'PKR',
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                    signDisplay: 'always'
                  })}
                </p>
              </div>
            )
          ))}
        </div>
      </div>

      {/* Reconciliation Verification */}
      {reconciliationVerdict.bankClosing !== null && reconciliationVerdict.companyClosing !== null ? (
        <div className="rounded-lg border p-5 space-y-4">
          <h4 className="text-sm font-semibold">Reconciliation Verification</h4>

          <div className="space-y-2">
            {/* Adjusted Company Book Balance */}
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold text-foreground">Adjusted Company Book Balance</span>
              <span className="font-mono text-base font-bold">{formatAmount(reconciliationVerdict.adjustedCompany ?? 0)}</span>
            </div>

            {/* Company Book Balance */}
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold text-foreground">Company Book Balance</span>
              <span className="font-mono text-base font-bold">{formatAmount(reconciliationVerdict.companyClosing)}</span>
            </div>
          </div>

          {/* Verdict */}
          <div className={`rounded-lg p-4 text-center ${
            reconciliationVerdict.isBalanced
              ? 'bg-green-50 border border-green-200'
              : 'bg-red-50 border border-red-200'
          }`}>
            {reconciliationVerdict.isBalanced ? (
              <div className="flex items-center justify-center gap-2 text-green-800">
                <CheckCircle2 className="size-5" />
                <p className="text-sm font-semibold">
                  Balanced — The books match! Difference: {formatAmount(0)}
                </p>
              </div>
            ) : (
              <div className="flex items-center justify-center gap-2 text-red-800">
                <XCircle className="size-5" />
                <p className="text-sm font-semibold">
                  Not Balanced — Difference: {formatAmount(reconciliationVerdict.difference ?? 0)}
                </p>
              </div>
            )}
          </div>
        </div>
      ) : (
        /* Missing totals */
        <div className="rounded-lg border border-yellow-200 bg-yellow-50 p-4 text-center">
          <div className="flex items-center justify-center gap-2 text-yellow-800">
            <AlertTriangle className="size-5" />
            <p className="text-sm font-semibold">Verification Unavailable</p>
          </div>
          <p className="text-xs text-yellow-700 mt-1">
            {reconciliationVerdict.bankClosing === null && reconciliationVerdict.companyClosing === null
              ? 'Both Bank Closing Balance and Company Book Balance are missing.'
              : reconciliationVerdict.bankClosing === null
              ? 'Bank Closing Balance is missing from the bank statement.'
              : 'Company Book Balance is missing from the company records.'}
          </p>
        </div>
      )}

      <ManualReconciliation
        transactions={categorizedData}
        selectedItems={selectedItems}
        onToggleSelection={onToggleSelection}
        onReconcile={onReconcile}
      />
    </div>
  );
}

/**
 * Category Section component for displaying a single category of transactions
 * Reuses existing table design patterns from DiscrepancyList component
 */
interface CategorySectionProps {
  title: string;
  transactions: CategorizedTransaction[];
  count: number;
  selectedItems?: Set<string>;
  onToggleSelection?: (itemId: string) => void;
}

function CategorySection({ title, transactions, count, selectedItems, onToggleSelection }: CategorySectionProps) {
  if (count === 0) {
    return (
      <div className="rounded-lg border border-green-200 bg-green-50 px-4 py-6 text-center">
        <p className="text-sm font-medium text-green-800">
          {title}: No transactions in this category
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border">
      <div className="flex items-center justify-between px-4 py-3 bg-muted/40 border-b">
        <h3 className="text-sm font-semibold">{title}</h3>
        <span className="text-sm text-muted-foreground bg-background px-2 py-1 rounded">
          {count} {count === 1 ? 'transaction' : 'transactions'}
        </span>
      </div>

      {/* Column headers */}
      <div className="flex items-center px-4 py-2 text-xs font-medium text-muted-foreground border-b bg-muted/20">
        {onToggleSelection && <div className="w-[40px]" />}
        <div className="flex-[180px]">Date</div>
        <div className="flex-[300px]">Details</div>
        <div className="w-[130px] text-right">Amount</div>
        <div className="w-[100px] text-center">Source</div>
        <div className="w-[90px] text-center">From Past</div>
      </div>

      <div className="divide-y">
        {transactions.map((transaction) => (
          <div
            key={transaction.itemId}
            className={`flex items-center px-4 py-3 hover:bg-muted/30 ${
              selectedItems?.has(transaction.itemId) ? 'bg-blue-50/50' : ''
            } ${
              transaction.from_past ? 'bg-purple-50' : ''
            }`}
          >
            {onToggleSelection && (
              <div className="w-[40px] flex items-center justify-center">
                <input
                  type="checkbox"
                  checked={selectedItems?.has(transaction.itemId) ?? false}
                  onChange={() => onToggleSelection(transaction.itemId)}
                  className="size-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
                  aria-label={`Select transaction on ${transaction['Transaction_date']}`}
                />
              </div>
            )}
            <div className="flex-[180px] font-mono text-sm">
              {transaction['Transaction_date']}
            </div>
            <div className="flex-[300px] text-sm">
              {transaction['Transaction Detail']}
            </div>
            <div className={`w-[130px] text-right font-mono text-sm font-semibold ${
              transaction.displayAmount >= 0 ? 'text-green-600' : 'text-red-600'
            }`}>
              {transaction.displayValue}
            </div>
            <div className="w-[100px] text-center">
              <span
                className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                  transaction.FROM === 'Bank'
                    ? 'border-blue-200 bg-blue-50 text-blue-800'
                    : 'border-emerald-200 bg-emerald-50 text-emerald-800'
                }`}
              >
                {transaction.FROM}
              </span>
            </div>
            <div className="w-[90px] text-center">
              {transaction.from_past && (
                <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium border-purple-200 bg-purple-100 text-purple-800">
                  Yes
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ