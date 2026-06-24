'use client';

import { ReconciliationResult } from '@/types/reconciliation.types';
import { DiscrepancyList } from '@/components/results/DiscrepancyList';
import { Badge } from '@/components/ui/badge';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { CheckCircle2, Clock, FileSearch, RotateCcw } from 'lucide-react';

interface ReconciliationResultsProps {
  result: ReconciliationResult;
  onStartNew?: () => void;
}

function formatTimestamp(timestamp: string): string {
  return new Date(timestamp).toLocaleString('en-US', {
    dateStyle: 'medium',
    timeStyle: 'short',
  });
}

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms} ms`;
  return `${(ms / 1000).toFixed(2)} s`;
}

function statusVariant(status: ReconciliationResult['processing_status']) {
  switch (status) {
    case 'completed':
      return 'default' as const;
    case 'partial':
      return 'secondary' as const;
    case 'error':
      return 'destructive' as const;
    default:
      return 'outline' as const;
  }
}

export function ReconciliationResults({ result, onStartNew }: ReconciliationResultsProps) {
  const { request_id, processing_status, processing_timestamp, summary } = result;
  const discrepancies = result.results.discrepancies;

  const summaryItems = [
    { label: 'Bank Transactions', value: summary.total_bank_transactions },
    { label: 'Company Transactions', value: summary.total_company_transactions },
    { label: 'Total Discrepancies', value: summary.total_discrepancies },
    { label: 'Bank Only', value: summary.bank_only_discrepancies },
    { label: 'Company Only', value: summary.company_only_discrepancies },
    { label: 'Matched Pairs Removed', value: summary.opposite_pairs_removed },
    { label: 'Processing Duration', value: formatDuration(summary.processing_duration_ms) },
    { label: 'PDF Processing', value: formatDuration(summary.pdf_processing_time_ms) },
    { label: 'Excel Processing', value: formatDuration(summary.excel_processing_time_ms) },
    {
      label: 'Concurrent Processing',
      value: summary.concurrent_processing ? 'Yes' : 'No',
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Reconciliation Results</h2>
          <p className="text-sm text-muted-foreground">
            Review processing details and unmatched transactions below.
          </p>
        </div>
        {onStartNew && (
          <Button variant="outline" onClick={onStartNew}>
            <RotateCcw data-icon="inline-start" />
            New Reconciliation
          </Button>
        )}
      </div>

      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="space-y-1">
              <CardTitle className="flex items-center gap-2">
                <FileSearch className="size-4" />
                Request Details
              </CardTitle>
              <CardDescription>Processing metadata for this reconciliation run</CardDescription>
            </div>
            <Badge variant={statusVariant(processing_status)} className="capitalize">
              {processing_status === 'completed' && <CheckCircle2 data-icon="inline-start" />}
              {processing_status}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2">
          <div className="rounded-lg border bg-muted/30 p-4">
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Request ID
            </p>
            <p className="mt-1 break-all font-mono text-sm">{request_id}</p>
          </div>
          <div className="rounded-lg border bg-muted/30 p-4">
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Processing Timestamp
            </p>
            <p className="mt-1 flex items-center gap-2 text-sm">
              <Clock className="size-4 text-muted-foreground" />
              {formatTimestamp(processing_timestamp)}
            </p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Summary</CardTitle>
          <CardDescription>Overview of transactions processed and reconciliation outcome</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {summaryItems.map((item) => (
              <div
                key={item.label}
                className="rounded-lg border px-4 py-3"
              >
                <p className="text-xs text-muted-foreground">{item.label}</p>
                <p className="mt-1 text-lg font-semibold">{item.value}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Discrepancies</CardTitle>
          <CardDescription>
            Transactions present in one source but not matched in the other
          </CardDescription>
        </CardHeader>
        <CardContent>
          <DiscrepancyList discrepancies={discrepancies} />
        </CardContent>
      </Card>
    </div>
  );
}
