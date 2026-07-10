/*
 * بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ
 * Reconciliation Totals Component
 * Feature: 002-reconciliation-totals
 *
 * Displays Bank Net Total, Company Net Total, adjusted totals with discrepancy
 * adjustments, and the reconciliation verdict (balanced / not balanced).
 */

'use client';

import { useMemo } from 'react';
import { NetTotalValue, DiscrepancyTransaction } from '@/types/reconciliation.types';
import { TransactionCategory } from '@/types/categorization.types';
import { categorizeTransaction, formatAmount } from '@/lib/utils/categorizationUtils';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AlertTriangle, CheckCircle2, XCircle } from 'lucide-react';

interface ReconciliationTotalsProps {
  bankNetTotal?: NetTotalValue;
  companyNetTotal?: NetTotalValue;
  discrepancies: DiscrepancyTransaction[];
}

/**
 * وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
 * Categorize discrepancies and compute adjusted totals + verdict
 */
function useTotalsCalculation(
  bankNetTotal: NetTotalValue | undefined,
  companyNetTotal: NetTotalValue | undefined,
  discrepancies: DiscrepancyTransaction[]
) {
  return useMemo(() => {
    // Sum discrepancy amounts by category using RAW signed values
    // Raw values already have correct sign: positive=credit, negative=debit
    // Adding a signed value naturally handles add (positive) / subtract (negative)
    const categorySums: Record<string, number> = {
      [TransactionCategory.UNCLEARED_CHECKS]: 0,
      [TransactionCategory.UNPRESENTED_CHECKS]: 0,
      [TransactionCategory.BANK_DEBITED_NOT_CREDITED]: 0,
      [TransactionCategory.BANK_CREDITED_NOT_DEBITED]: 0,
    };

    for (const d of discrepancies) {
      const category = categorizeTransaction(d.FROM, d['Debit/Credit']);
      // Use raw signed value — positive adds, negative subtracts
      categorySums[category] = (categorySums[category] || 0) + d['Debit/Credit'];
    }

    // Raw totals
    const bankRaw = bankNetTotal?.status === 'found' ? bankNetTotal.value ?? 0 : null;
    const companyRaw = companyNetTotal?.status === 'found' ? companyNetTotal.value ?? 0 : null;

    // RAW discrepancy adjustments (signed — positive adds, negative subtracts)
    // Used only for internal math (adjusted totals)
    const unclearedChecks = categorySums[TransactionCategory.UNCLEARED_CHECKS] || 0;
    const unpresentedChecks = categorySums[TransactionCategory.UNPRESENTED_CHECKS] || 0;
    const bankCreditedNotDebited = categorySums[TransactionCategory.BANK_DEBITED_NOT_CREDITED] || 0;
    const bankDebitedNotCredited = categorySums[TransactionCategory.BANK_CREDITED_NOT_DEBITED] || 0;

    // DISPLAY adjustments with enforced sign convention per the accounting rules:
    //   - Unpresented Checks:           always negative (Company debits not yet presented)
    //   - Uncleared Checks:             always negative (Company credits not yet cleared)
    //   - Bank Credited Not Debited:    always negative (Bank credits not in cash book)
    //   - Bank Debited Not Credited:    always positive (Bank debits not in cash book)
    const displayUnclearedChecks = -Math.abs(unclearedChecks);
    const displayUnpresentedChecks = -Math.abs(unpresentedChecks);
    const displayBankCreditedNotDebited = -Math.abs(bankCreditedNotDebited);
    const displayBankDebitedNotCredited = Math.abs(bankDebitedNotCredited);

    // Adjusted totals: add signed values (positive→add, negative→subtract)
    const adjustedBank = bankRaw !== null ? bankRaw + unclearedChecks + unpresentedChecks : null;
    const adjustedCompany = companyRaw !== null ? companyRaw + bankCreditedNotDebited + bankDebitedNotCredited : null;

    // Verdict
    let isBalanced: boolean | null = null;
    let difference: number | null = null;
    let higherSide: 'Bank' | 'Company' | null = null;

    if (adjustedBank !== null && adjustedCompany !== null) {
      difference = Math.abs(adjustedBank - adjustedCompany);
      isBalanced = difference < 0.001;
      if (!isBalanced) {
        higherSide = adjustedBank > adjustedCompany ? 'Bank' : 'Company';
      }
    }

    return {
      bankRaw,
      companyRaw,
      unclearedChecks,
      unpresentedChecks,
      bankCreditedNotDebited,
      bankDebitedNotCredited,
      displayUnclearedChecks,
      displayUnpresentedChecks,
      displayBankCreditedNotDebited,
      displayBankDebitedNotCredited,
      adjustedBank,
      adjustedCompany,
      isBalanced,
      difference,
      higherSide,
      bankStatus: bankNetTotal?.status,
      companyStatus: companyNetTotal?.status,
    };
  }, [bankNetTotal, companyNetTotal, discrepancies]);
}

function StatusBadge({ status }: { status: string | undefined }) {
  if (status === 'found') {
    return <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">Found</Badge>;
  }
  if (status === 'missing') {
    return <Badge variant="outline" className="bg-yellow-50 text-yellow-700 border-yellow-200">
      <AlertTriangle className="mr-1 size-3" /> Missing
    </Badge>;
  }
  if (status === 'invalid') {
    return <Badge variant="outline" className="bg-red-50 text-red-700 border-red-200">
      <AlertTriangle className="mr-1 size-3" /> Invalid
    </Badge>;
  }
  return null;
}

export function ReconciliationTotals({
  bankNetTotal,
  companyNetTotal,
  discrepancies,
}: ReconciliationTotalsProps) {
  const calc = useTotalsCalculation(bankNetTotal, companyNetTotal, discrepancies);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          Reconciliation Totals & Verification
        </CardTitle>
        <CardDescription>
          Adjusted totals after applying discrepancies and automatic verification
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Raw Totals */}
        <div className="grid gap-4 sm:grid-cols-2">
          {/* Bank Net Total */}
          <div className="rounded-lg border p-4 space-y-2">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium text-muted-foreground">Bank Net Total</p>
              <StatusBadge status={calc.bankStatus} />
            </div>
            <p className="text-2xl font-bold">
              {calc.bankRaw !== null ? formatAmount(calc.bankRaw) : '—'}
            </p>
            <p className="text-xs text-muted-foreground">
              Last Balance value from bank statement
            </p>

            {/* Error states (US2) */}
            {calc.bankStatus === 'missing' && (
              <p className="text-xs text-yellow-700 flex items-center gap-1">
                <AlertTriangle className="size-3" />
                Balance column not found in bank statement data
              </p>
            )}
            {calc.bankStatus === 'invalid' && (
              <p className="text-xs text-red-700 flex items-center gap-1">
                <AlertTriangle className="size-3" />
                Balance value could not be parsed from bank statement
              </p>
            )}
          </div>

          {/* Company Net Total */}
          <div className="rounded-lg border p-4 space-y-2">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium text-muted-foreground">Company Net Total</p>
              <StatusBadge status={calc.companyStatus} />
            </div>
            <p className="text-2xl font-bold">
              {calc.companyRaw !== null ? formatAmount(calc.companyRaw) : '—'}
            </p>
            <p className="text-xs text-muted-foreground">
              Last Aggregated Total value from company records
            </p>

            {/* Error states (US2) */}
            {calc.companyStatus === 'missing' && (
              <p className="text-xs text-yellow-700 flex items-center gap-1">
                <AlertTriangle className="size-3" />
                Aggregated Total column not found or not specified
              </p>
            )}
            {calc.companyStatus === 'invalid' && (
              <p className="text-xs text-red-700 flex items-center gap-1">
                <AlertTriangle className="size-3" />
                Aggregated Total value could not be parsed from company records
              </p>
            )}
          </div>
        </div>

        {/* Discrepancy Adjustments */}
        <div className="rounded-lg border bg-muted/30 p-4 space-y-3">
          <p className="text-sm font-semibold">Discrepancy Adjustments</p>

          <div className="grid gap-3 sm:grid-cols-2">
            {/* Bank adjustments: Uncleared checks (positive→add), Unpresented checks (negative→subtract) */}
            <div className="space-y-1">
              <p className="text-xs font-medium text-muted-foreground">Bank Net Total Adjustments</p>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span>Uncleared Checks</span>
                  <span className="font-mono">{formatAmount(calc.displayUnclearedChecks)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Unpresented Checks</span>
                  <span className="font-mono">{formatAmount(calc.displayUnpresentedChecks)}</span>
                </div>
                <div className="flex justify-between border-t pt-1 font-semibold">
                  <span>Net Adjustment</span>
                  <span className="font-mono">{formatAmount(calc.displayUnclearedChecks + calc.displayUnpresentedChecks)}</span>
                </div>
              </div>
            </div>

            {/* Company adjustments: Credited not debited (positive→add), Debited not credited (negative→subtract) */}
            <div className="space-y-1">
              <p className="text-xs font-medium text-muted-foreground">Company Net Total Adjustments</p>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span>Bank Debited But Not Credited</span>
                  <span className="font-mono">{formatAmount(calc.displayBankDebitedNotCredited)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Bank Credited But Not Debited</span>
                  <span className="font-mono">{formatAmount(calc.displayBankCreditedNotDebited)}</span>
                </div>
                <div className="flex justify-between border-t pt-1 font-semibold">
                  <span>Net Adjustment</span>
                  <span className="font-mono">{formatAmount(calc.displayBankDebitedNotCredited + calc.displayBankCreditedNotDebited)}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Adjusted Totals and Verdict (US3) */}
        {calc.adjustedBank !== null && calc.adjustedCompany !== null ? (
          <>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
                <p className="text-sm font-medium text-blue-800">Adjusted Bank Total</p>
                <p className="text-2xl font-bold text-blue-900">
                  {formatAmount(calc.adjustedBank)}
                </p>
              </div>
              <div className="rounded-lg border border-purple-200 bg-purple-50 p-4">
                <p className="text-sm font-medium text-purple-800">Adjusted Company Total</p>
                <p className="text-2xl font-bold text-purple-900">
                  {formatAmount(calc.adjustedCompany)}
                </p>
              </div>
            </div>

            {/* Reconciliation Verdict */}
            <div className={`rounded-lg border p-4 text-center ${
              calc.isBalanced
                ? 'bg-green-50 border-green-200'
                : 'bg-red-50 border-red-200'
            }`}>
              {calc.isBalanced ? (
                <div className="space-y-1">
                  <div className="flex items-center justify-center gap-2 text-green-800">
                    <CheckCircle2 className="size-6" />
                    <p className="text-lg font-bold">Reconciliation Successful, Balanced</p>
                  </div>
                  <p className="text-sm text-green-700">
                    Difference: {formatAmount(0)} — Both adjusted totals match
                  </p>
                </div>
              ) : (
                <div className="space-y-1">
                  <div className="flex items-center justify-center gap-2 text-red-800">
                    <XCircle className="size-6" />
                    <p className="text-lg font-bold">Reconciliation Not Balanced</p>
                  </div>
                  <p className="text-sm text-red-700">
                    Difference: {formatAmount(calc.difference ?? 0)} — {' '}
                    {calc.higherSide} adjusted total is higher by {formatAmount(calc.difference ?? 0)}
                  </p>
                </div>
              )}
            </div>
          </>
        ) : (
          /* Partial or no totals available — show appropriate message */
          <div className="rounded-lg border border-yellow-200 bg-yellow-50 p-4 text-center">
            <div className="flex items-center justify-center gap-2 text-yellow-800">
              <AlertTriangle className="size-5" />
              <p className="font-semibold">Verification Unavailable</p>
            </div>
            <p className="text-sm text-yellow-700 mt-1">
              {calc.bankRaw !== null && calc.companyRaw === null
                ? 'Company Net Total is missing. Provide the Aggregated Total column name to enable reconciliation verification.'
                : calc.bankRaw === null && calc.companyRaw !== null
                ? 'Bank Net Total is missing. Balance column could not be extracted from the bank statement.'
                : 'Both Bank Net Total and Company Net Total are missing. Check your uploaded files and column mappings.'}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

/*
 * وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
 */
