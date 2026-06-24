'use client';

import { DiscrepancyTransaction } from '@/types/reconciliation.types';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

interface DiscrepancyListProps {
  discrepancies: DiscrepancyTransaction[];
}

function formatAmount(amount: number): string {
  const formatted = Math.abs(amount).toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  return amount >= 0 ? `+${formatted}` : `-${formatted}`;
}

/** Bank statement amounts use inverted sign convention — flip for display only */
function getDisplayAmount(discrepancy: DiscrepancyTransaction): number {
  const raw = discrepancy['Debit/Credit'];
  return discrepancy.FROM === 'Bank' ? -raw : raw;
}

export function DiscrepancyList({ discrepancies }: DiscrepancyListProps) {
  if (!discrepancies || discrepancies.length === 0) {
    return (
      <div className="rounded-lg border border-green-200 bg-green-50 px-4 py-6 text-center">
        <p className="text-sm font-medium text-green-800">
          Perfect match — no discrepancies found between bank statement and company records.
        </p>
      </div>
    );
  }

  const bankCount = discrepancies.filter((d) => d.FROM === 'Bank').length;
  const companyCount = discrepancies.filter((d) => d.FROM === 'Company').length;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-muted-foreground">
          Found <span className="font-semibold text-foreground">{discrepancies.length}</span> discrepancies
          requiring review.
        </p>
        <div className="flex gap-2">
          <Badge variant="secondary" className="bg-blue-100 text-blue-800">
            Bank: {bankCount}
          </Badge>
          <Badge variant="secondary" className="bg-emerald-100 text-emerald-800">
            Company: {companyCount}
          </Badge>
        </div>
      </div>

      <div className="rounded-lg border">
        <Table>
          <TableHeader>
            <TableRow className="bg-muted/40 hover:bg-muted/40">
              <TableHead className="w-[120px]">Date</TableHead>
              <TableHead>Transaction Detail</TableHead>
              <TableHead className="w-[160px] text-right">Amount</TableHead>
              <TableHead className="w-[110px] text-center">Source</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {discrepancies.map((discrepancy, index) => {
              const displayAmount = getDisplayAmount(discrepancy);
              const isCredit = displayAmount >= 0;
              return (
                <TableRow key={`${discrepancy['Transaction_date']}-${index}`}>
                  <TableCell className="font-medium">
                    {discrepancy['Transaction_date']}
                  </TableCell>
                  <TableCell className="max-w-md whitespace-normal">
                    {discrepancy['Transaction Detail']}
                  </TableCell>
                  <TableCell
                    className={`text-right font-mono font-semibold ${
                      isCredit ? 'text-green-600' : 'text-red-600'
                    }`}
                  >
                    {formatAmount(displayAmount)}
                  </TableCell>
                  <TableCell className="text-center">
                    <Badge
                      variant="outline"
                      className={
                        discrepancy.FROM === 'Bank'
                          ? 'border-blue-200 bg-blue-50 text-blue-800'
                          : 'border-emerald-200 bg-emerald-50 text-emerald-800'
                      }
                    >
                      {discrepancy.FROM}
                    </Badge>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
