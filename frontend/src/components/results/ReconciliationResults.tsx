'use client';

import { useState, useCallback, useMemo, useRef } from 'react';
import { useSession } from 'next-auth/react';
import { ReconciliationResult, DiscrepancyTransaction } from '@/types/reconciliation.types';
import { CategorizedResults } from '@/components/results/CategorizedResults';
import { useReconciliationType } from '@/components/providers/reconciliation-type-provider';
import { Badge } from '@/components/ui/badge';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { CheckCircle2, Clock, FileSearch, MessagesSquare, RotateCcw, Save, Wand2 } from 'lucide-react';
import {
  generateItemId,
  getDisplayAmount
} from '@/lib/utils/categorizationUtils';
import { formatAmount } from '@/lib/utils/categorizationUtils';
import { cloudHistoryClient } from '@/lib/api/cloudHistoryClient';
import type { CloudHistoryEntry } from '@/types/cloud-history.types';
import { Input } from '@/components/ui/input';
import { AdvisorPanel } from '@/components/advisor/AdvisorPanel';
import { AdvisorChat } from '@/components/advisor/AdvisorChat';
import { runAdvisorReconcile, cancelAdvisorRun } from '@/lib/api/advisorClient';
import type {
  AdvisorDiscrepancy,
  AdvisorResponse,
  BalanceContext,
  BalancePoint,
} from '@/types/advisor.types';

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
  const { reconciliationType } = useReconciliationType();
  const { request_id, processing_status, processing_timestamp, summary } = result;
  // Graceful guard: the backend may return a partial/error result without a
  // discrepancies array — never crash the page over a missing field.
  const [discrepancies, setDiscrepancies] = useState<DiscrepancyTransaction[]>(
    Array.isArray(result.results?.discrepancies) ? result.results.discrepancies : []
  );
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

  // ---- AI Reconciler Advisor (Subh al Baqaya, feature 007) ----
  // State is component-local (FR-013): resets on new reconciliation / fresh
  // page load because the component remounts with a new result.
  const [advisorResponse, setAdvisorResponse] = useState<AdvisorResponse | null>(null);
  const [advisorRunning, setAdvisorRunning] = useState(false);
  const [advisorError, setAdvisorError] = useState<string | null>(null);
  const advisorAbortRef = useRef<AbortController | null>(null);

  // Stable backend keys (discrepancy_id) for the items sent to the agent.
  const liveKeys = useMemo(
    () =>
      new Set<string>(
        discrepancies.map((d) => d.discrepancy_id).filter((id): id is string => Boolean(id))
      ),
    [discrepancies]
  );

  const buildBalanceContext = useCallback(
    (items: DiscrepancyTransaction[]): BalanceContext => {
      let bankRunning = 0;
      let companyRunning = 0;
      const points: BalancePoint[] = items.map((d, index) => {
        const amount = d['Debit/Credit'] ?? 0;
        if (d.FROM === 'Company') {
          companyRunning += amount;
        } else {
          bankRunning += amount;
        }
        return {
          index: index + 1,
          discrepancy_id: d.discrepancy_id ?? '',
          bank_running: bankRunning,
          company_running: companyRunning,
          net: bankRunning + companyRunning,
        };
      });
      return {
        points,
        bank_balance: bankRunning,
        company_balance: companyRunning,
      };
    },
    []
  );

  const buildAdvisorDiscrepancies = useCallback(
    (items: DiscrepancyTransaction[]): AdvisorDiscrepancy[] =>
      items.map((d) => ({
        discrepancy_id: d.discrepancy_id ?? '',
        Transaction_date: d['Transaction_date'],
        // Safe underscore wire key; the raw discrepancy dict uses the spaced
        // "Transaction Detail" — mapped here at the boundary.
        Transaction_Detail: d['Transaction Detail'],
        'Debit/Credit': d['Debit/Credit'],
        FROM: d.FROM,
        from_past: d.from_past,
      })),
    []
  );

  const handleRunAdvisor = useCallback(async () => {
    const token = (session?.user as { access_token?: string } | undefined)?.access_token;
    if (!token) {
      setAdvisorError('Not authenticated. Please sign in again.');
      return;
    }
    if (discrepancies.length === 0) return;

    setAdvisorRunning(true);
    setAdvisorError(null);
    setAdvisorResponse(null);

    const controller = new AbortController();
    advisorAbortRef.current = controller;

    try {
      const request = {
        request_id,
        discrepancies: buildAdvisorDiscrepancies(discrepancies),
        context: buildBalanceContext(discrepancies),
        history: [],
        question: null,
      };
      const response = await runAdvisorReconcile(
        token,
        request,
        undefined,
        controller.signal
      );
      setAdvisorResponse(response);
    } catch (err) {
      if (err instanceof DOMException && err.name === 'AbortError') {
        setAdvisorError('Agent run cancelled.');
      } else {
        setAdvisorError(
          err instanceof Error ? err.message : 'The agent is unable to respond due to a technical failure.'
        );
      }
    } finally {
      setAdvisorRunning(false);
      advisorAbortRef.current = null;
    }
  }, [session, discrepancies, request_id, buildAdvisorDiscrepancies, buildBalanceContext]);

  const handleCancelAdvisor = useCallback(() => {
    advisorAbortRef.current?.abort();
    cancelAdvisorRun(request_id);
    setAdvisorRunning(false);
  }, [request_id]);

  // Suggestion-reconcile: remove exactly the suggested items from the live
  // main list — frontend-only (FR-010), mirroring handleReconcile's filter so
  // the live list, manual reconcile, and Complete Reconciliation stay in sync.
  const handleAdvisorReconcile = useCallback(
    (keys: string[]) => {
      setDiscrepancies(prev => {
        const removed = new Set(keys);
        return prev.filter(d => !removed.has(d.discrepancy_id ?? ''));
      });
      setSelectedItems(new Set());
    },
    []
  );

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
        category: categorizeDiscrepancy(d.FROM, d['Debit/Credit'], reconciliationType),
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
  }, [discrepancies, saveName, session, reconciliationType]);

  // Helper: determine category from source, amount, and reconciliation mode.
  // Wire values carry the pure source-specific convention (no flips):
  //   Bank:    credit = +, debit = -
  //   Company: credit = -, debit = +  (Unpresented = -, Uncleared = +)
  //   Vendor:  credit = -, debit = +  (source-side rows)
  function categorizeDiscrepancy(from: string, amount: number, mode: 'bank' | 'vendor' = 'bank'): string {
    if (mode === 'vendor') {
      // Vendor ledger: source-side (Bank) rows use vendor convention — a
      // positive amount = debited but not credited; a negative one =
      // credited but not debited.
      if (from === 'Company' && amount < 0) return 'Unpresented Checks';
      if (from === 'Company' && amount >= 0) return 'Uncleared Checks';
      if (from === 'Bank' && amount >= 0) return 'Vendor Debited but not Credited in Cashbook';
      return 'Vendor Credited But not Debited in Cashbook';
    }
    if (from === 'Company' && amount < 0) return 'Unpresented Checks';
    if (from === 'Company' && amount >= 0) return 'Uncleared Checks';
    if (from === 'Bank' && amount >= 0) return 'Bank Credited But not Debited in Cashbook';
    return 'Bank Debited But not Credited in Cashbook';
  }

  const summaryItems = [
    { label: 'Bank Transactions', value: summary.total_bank_transactions },
    { label: 'Company Transactions', value: summary.total_company_transactions },
    { label: 'Total Discrepancies', value: summary.total_discrepancies },
    { label: 'Bank Only', value: summary.bank_only_discrepancies },
    { label: 'Company Only', value: summary.company_only_discrepancies },
    { label: 'Matched Pairs Removed', value: summary.opposite_pairs_removed },
    { label: 'Pair-Mate Pairs Removed', value: summary.pair_mate_pairs_removed ?? 0 },
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
        {discrepancies.length > 0 && (
          <Button
            variant="default"
            onClick={advisorRunning ? handleCancelAdvisor : handleRunAdvisor}
            disabled={advisorRunning && !advisorAbortRef.current}
          >
            <Wand2 data-icon="inline-start" />
            {advisorRunning ? 'Cancel Agent Run' : 'Reconcile With Agent'}
          </Button>
        )}
      </div>

      {advisorError && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {advisorError}
        </div>
      )}

      {(advisorResponse || advisorRunning) && (
        <AdvisorPanel
          advisorResponse={advisorResponse}
          liveKeys={liveKeys}
          onReconcile={handleAdvisorReconcile}
          isRunning={advisorRunning}
        />
      )}

      {advisorResponse && !advisorRunning && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MessagesSquare className="size-4" />
              Ask the Agent
            </CardTitle>
            <CardDescription>
              Follow-up questions about the reconciliation — the agent always
              sees the current discrepancies list.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <AdvisorChat
              token={
                (session?.user as { access_token?: string } | undefined)
                  ?.access_token ?? ''
              }
              requestId={request_id}
              discrepancies={discrepancies}
              buildDiscrepancies={buildAdvisorDiscrepancies}
              buildBalanceContext={buildBalanceContext}
            />
          </CardContent>
        </Card>
      )}

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
