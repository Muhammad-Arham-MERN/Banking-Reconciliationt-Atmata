'use client';

import { useState, useCallback, useMemo } from 'react';
import { useSession } from 'next-auth/react';
import { ReconciliationResult } from '@/types/reconciliation.types';
import { CategorizedResults } from '@/components/results/CategorizedResults';
import { Badge } from '@/components/ui/badge';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { CheckCircle2, Clock, FileSearch, RotateCcw, Save } from 'lucide-react';
import {
  generateItemId,
  getDisplayAmount
} from '@/lib/utils/categorizationUtils';
import { formatAmount } from '@/lib/utils/categorizationUtils';
import { cloudHistoryClient } from '@/lib/api/cloudHistoryClient';
import type { CloudHistoryEntry } from '@/types/cloud-history.types';
import { Input } from '@/components/ui/input';

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
  const { data: session } = useSession();
  const { request_id, processing_status, processing_timestamp, summary } = result;
  const [discrepancies, setDiscrepancies] = useState(result.results.discrepancies);
  const [selectedItems, setSelectedItems] = useState<Set<string>>(new Set());

  // Generate itemIds for each discrepancy for selection tracking
  const itemIds = useMemo(() => {
    return new Set(discrepancies.map((d, index) =>
      generateItemId(d['Transaction_date'], d.FROM, d['Debit/Credit'], index)
    ));
  }, [discrepancies]);

  // Clean up selectedItems when discrepancies change (remove stale selections)
  const validSelectedItems = useMemo(() => {
    const valid = new Set<string>();
    selectedItems.forEach(id => {
      if (itemIds.has(id)) valid.add(id);
    });
    return valid;
  }, [selectedItems, itemIds]);

  // Toggle selection callback
  const toggleSelection = useCallback((itemId: string) => {
    setSelectedItems(prev => {
      const next = new Set(prev);
      if (next.has(itemId)) {
        next.delete(itemId);
      } else {
        next.add(itemId);
      }
      return next;
    });
  }, []);

  // Handle manual reconciliation execution
  /**
   * وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
   * Execute manual reconciliation by removing selected items from the list
   */
  const handleReconcile = useCallback((selectedItemIds: Set<string>) => {
    setDiscrepancies(prev =>
      prev.filter((d, index) => {
        const itemId = generateItemId(d['Transaction_date'], d.FROM, d['Debit/Credit'], index);
        return !selectedItemIds.has(itemId);
      })
    );
    setSelectedItems(new Set());
  }, []);

  // Save history state
  const [saveName, setSaveName] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);

  const handleSave = useCallback(async () => {
    setIsSaving(true);
    setSaveMessage(null);
    setSaveError(null);

    const token = (session?.user as { access_token?: string } | undefined)?.access_token;
    if (!token) {
      setSaveError('Not authenticated. Please sign in again.');
      setIsSaving(false);
      return;
    }

    try {
      const fileData: CloudHistoryEntry[] = discrepancies.map(d => ({
        category: categorizeDiscrepancy(d.FROM, d['Debit/Credit']),
        transaction_details: d['Transaction Detail'],
        transaction_date: d['Transaction_date'],
        debit_credit_amount: d['Debit/Credit'],
      }));

      const fileName = saveName.trim() || `reconciliation-${Date.now()}`;

      const result = await cloudHistoryClient.saveCloudFile(token, fileName, fileData);
      setSaveMessage(`Saved "${result.file_name}" successfully`);
      setSaveName('');
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : 'Failed to save');
    } finally {
      setIsSaving(false);
    }
  }, [discrepancies, saveName, session]);

  // Helper: determine category from source and amount
  function categorizeDiscrepancy(from: string, amount: number): string {
    if (from === 'Company' && amount < 0) return 'Unpresented Checks';
    if (from === 'Company' && amount >= 0) return 'Uncleared Checks';
    if (from === 'Bank' && amount >= 0) return 'Bank Debited But not Credited in Cashbook';
    return 'Bank Credited But not Debited in Cashbook';
  }

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
          <CategorizedResults
            discrepancies={discrepancies}
            bankNetTotal={result.bank_net_total}
            companyNetTotal={result.company_net_total}
            selectedItems={validSelectedItems}
            onToggleSelection={toggleSelection}
            onReconcile={handleReconcile}
          />
        </CardContent>
      </Card>

      {/* Save to History section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Save className="size-4" />
            Save to History
          </CardTitle>
          <CardDescription>
            Save these discrepancies as a reconciliation history file for future reference
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center gap-3">
            <Input
              placeholder="Optional custom name (leave empty for auto date-time)"
              value={saveName}
              onChange={(e) => setSaveName(e.target.value)}
              disabled={isSaving}
              className="max-w-sm"
            />
            <Button
              onClick={handleSave}
              disabled={discrepancies.length === 0 || isSaving}
            >
              <Save data-icon="inline-start" />
              {isSaving ? 'Saving...' : 'Complete Reconciliation'}
            </Button>
          </div>
          {saveMessage && (
            <p className="text-sm text-green-600">{saveMessage}</p>
          )}
          {saveError && (
            <p className="text-sm text-red-600">{saveError}</p>
          )}
          {discrepancies.length === 0 && (
            <p className="text-xs text-muted-foreground">
              No discrepancies to save. Complete a reconciliation first.
            </p>
          )}
        </CardContent>
      </Card>

    </div>
  );
}

// وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
