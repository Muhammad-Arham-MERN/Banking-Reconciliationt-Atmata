'use client';

import { useState, useCallback, useMemo, useRef, useEffect } from 'react';
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
import {
  CheckCircle2,
  Clock,
  FileSearch,
  History,
  MessagesSquare,
  RotateCcw,
  Save,
  Undo2,
  Wand2,
} from 'lucide-react';
import {
  generateItemId,
  categorizeTransaction,
} from '@/lib/utils/categorizationUtils';
import { formatAmount, categoryLabel } from '@/lib/utils/categorizationUtils';
import { cloudHistoryClient } from '@/lib/api/cloudHistoryClient';
import { historyClient } from '@/lib/api/historyClient';
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
import { useHistoryState } from '@/lib/utils/useHistoryState';
import { PastReconciliationsDrawer } from '@/components/history/PastReconciliationsDrawer';
import {
  Drawer,
  DrawerContent,
  DrawerHeader,
  DrawerTitle,
  DrawerDescription,
  DrawerFooter,
  DrawerClose,
} from '@/components/ui/drawer';
import {
  TransactionCategory,
  ManualDiscrepancyDraft,
  DiscrepancyHistoryEntry,
  SortDirection,
  ViewMode,
} from '@/types/categorization.types';

interface ReconciliationResultsProps {
  result: ReconciliationResult;
  onStartNew?: () => void;
  /** PDF bank statement file name (shown in the summary, feature 9) */
  pdfFileName?: string;
  /** Excel company data file name (shown in the summary, feature 9) */
  excelFileName?: string;
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

// Helper: determine category from source, amount, and reconciliation mode.
// Wire values carry the pure source-specific convention (no flips):
//   Bank:    credit = +, debit = -
//   Company: credit = -, debit = +  (Unpresented = -, Uncleared = +)
//   Vendor:  credit = -, debit = +  (source-side rows)
function categorizeDiscrepancy(from: string, amount: number, mode: 'bank' | 'vendor' = 'bank'): string {
  if (mode === 'vendor') {
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

export function ReconciliationResults({ result, onStartNew, pdfFileName, excelFileName }: ReconciliationResultsProps) {
  const { data: session } = useSession();
  const { reconciliationType } = useReconciliationType();
  const { request_id, processing_status, processing_timestamp, summary } = result;

  // ---- Undoable live discrepancy list (feature 5) ----
  // The undo stack (past snapshots) is reset whenever the component remounts
  // (fresh reconciliation / page load), so it never leaks between runs.
  const {
    present: discrepancies,
    push: setDiscrepancies,
    undo: undoDiscrepancies,
  } = useHistoryState<DiscrepancyTransaction[]>(
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

  // ---- Discrepancy history (feature 5): every manual mutation is recorded
  // in-memory with a snapshot of the affected items, restorable from the
  // drawer. ---- 
  const [discrepancyHistory, setDiscrepancyHistory] = useState<DiscrepancyHistoryEntry[]>([]);

  const recordHistory = useCallback(
    (action: string, items: DiscrepancyTransaction[]) => {
      if (items.length === 0) return;
      setDiscrepancyHistory(prev => [
        {
          id: `dh-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
          timestamp: new Date().toISOString(),
          action,
          items,
        },
        ...prev,
      ]);
    },
    []
  );

  // ctrl+z undo (feature 5) — global to the results view, but ignored when
  // the focus is inside an input/textarea (typing in the manual-add popover,
  // search box, save-name field, etc.).
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (!(event.ctrlKey || event.metaKey) || event.key.toLowerCase() !== 'z') return;
      const target = event.target as HTMLElement | null;
      if (target && (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable)) {
        return;
      }
      event.preventDefault();
      if (undoDiscrepancies()) {
        setSelectedItems(new Set());
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [undoDiscrepancies]);

  // Handle manual reconciliation execution
  const handleReconcile = useCallback((selectedItemIds: Set<string>) => {
    // Compute kept/removed from the closure value — NOT inside the setState
    // updater, which React may invoke lazily and would empty the removed list.
    const removed: DiscrepancyTransaction[] = [];
    const kept = discrepancies.filter((d, index) => {
      const itemId = generateItemId(d['Transaction_date'], d.FROM, d['Debit/Credit'], index);
      const isSelected = selectedItemIds.has(itemId);
      if (isSelected) removed.push(d);
      return !isSelected;
    });
    setDiscrepancies(kept);
    recordHistory('Manual reconciliation', removed);
    setSelectedItems(new Set());
  }, [discrepancies, setDiscrepancies, recordHistory]);

  // ---- AI Reconciler Advisor (Subh al Baqaya, feature 007) ----
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
      const removedSet = new Set(keys);
      const removed: DiscrepancyTransaction[] = [];
      const kept = discrepancies.filter(d => {
        const isRemoved = removedSet.has(d.discrepancy_id ?? '');
        if (isRemoved) removed.push(d);
        return !isRemoved;
      });
      setDiscrepancies(kept);
      recordHistory('Agent suggestion', removed);
      setSelectedItems(new Set());
    },
    [discrepancies, setDiscrepancies, recordHistory]
  );

  // ---- Manual discrepancy addition (feature 8) ----
  const handleAddManualDiscrepancy = useCallback(
    (category: string, draft: ManualDiscrepancyDraft) => {
      // Category keys are the enum-form display titles — match with
      // categoryLabel so bank/vendor mode swaps are handled uniformly.
      const unpresentedLabel = categoryLabel(TransactionCategory.UNPRESENTED_CHECKS, reconciliationType);
      const unclearedLabel = categoryLabel(TransactionCategory.UNCLEARED_CHECKS, reconciliationType);
      const creditedLabel = categoryLabel(TransactionCategory.BANK_CREDITED_NOT_DEBITED, reconciliationType);
      const debitedLabel = categoryLabel(TransactionCategory.BANK_DEBITED_NOT_CREDITED, reconciliationType);

      const isBankSide = category === creditedLabel || category === debitedLabel;

      let from: 'Bank' | 'Company';
      let amount: number;

      if (category === unpresentedLabel) {
        from = 'Company';
        amount = -Math.abs(draft.amount);
      } else if (category === unclearedLabel) {
        from = 'Company';
        amount = Math.abs(draft.amount);
      } else if (isBankSide && category === creditedLabel) {
        from = 'Bank';
        amount = Math.abs(draft.amount);
      } else {
        from = 'Bank';
        amount = -Math.abs(draft.amount);
      }

      const manual: DiscrepancyTransaction = {
        'Transaction_date': draft.date || new Date().toISOString().slice(0, 10),
        'Transaction Detail': draft.details.trim(),
        'Debit/Credit': amount,
        FROM: from,
        from_past: draft.fromPast,
        discrepancy_id: `manual-${Date.now()}`,
      };

      setDiscrepancies(prev => [...prev, manual]);
      setSelectedItems(new Set());
    },
    [setDiscrepancies, reconciliationType]
  );

  // ---- Restore from Discrepancies History (feature 5) ----
  const handleRestoreItems = useCallback(
    (entryId: string, items: DiscrepancyTransaction[]) => {
      setDiscrepancies(prev => {
        const existingKeys = new Set(
          prev.map(d => `${d['Transaction_date']}|${d['Transaction Detail']}|${d['Debit/Credit']}|${d.FROM}`)
        );
        const toRestore = items.filter(d => {
          const key = `${d['Transaction_date']}|${d['Transaction Detail']}|${d['Debit/Credit']}|${d.FROM}`;
          if (existingKeys.has(key)) return false;
          existingKeys.add(key);
          return true;
        });
        return [...prev, ...toRestore];
      });
      // Remove the entry from the history drawer after restoring.
      setDiscrepancyHistory(prev => prev.filter(e => e.id !== entryId));
      setSelectedItems(new Set());
    },
    [setDiscrepancies]
  );

  // ---- Save history state ----
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

  // ---- Past Reconciliations drawer (shared with the upload pages) ----
  const [reconHistoryOpen, setReconHistoryOpen] = useState(false);
  const [reconHistoryError, setReconHistoryError] = useState<string | null>(null);

  const handleOpenReconHistory = useCallback(() => {
    setReconHistoryOpen(true);
  }, []);

  const handleLoadPastFile = useCallback(
    async (fileName: string) => {
      // "None" — clear the selection without merging anything.
      if (!fileName) return;
      const token = (session?.user as { access_token?: string } | undefined)?.access_token;
      if (!token) return;
      try {
        const pastData = await historyClient.loadHistory(fileName);
        const past = pastData.discrepancies as {
          transaction_details: string;
          transaction_date: string;
          debit_credit_amount: number;
          category: string;
        }[];
        const mapped: DiscrepancyTransaction[] = past.map(p => ({
          'Transaction_date': p.transaction_date,
          'Transaction Detail': p.transaction_details,
          'Debit/Credit': p.debit_credit_amount,
          'FROM': p.category && p.category.includes('Bank') ? 'Bank' : 'Company',
          from_past: true,
        }));
        setDiscrepancies(prev => {
          const currentKeys = new Set(
            prev.map(d => `${d['Transaction Detail']}|${d['Transaction_date']}`)
          );
          const toAdd = mapped.filter(p => {
            const key = `${p['Transaction Detail']}|${p['Transaction_date']}`;
            if (currentKeys.has(key)) return false;
            currentKeys.add(key);
            return true;
          });
          const combined = [...prev, ...toAdd];
          combined.sort((a, b) => (a['Transaction_date'] ?? '').localeCompare(b['Transaction_date'] ?? ''));
          return combined;
        });
        setReconHistoryOpen(false);
      } catch (err) {
        setReconHistoryError(err instanceof Error ? err.message : 'Failed to load past reconciliation');
      }
    },
    [session, setDiscrepancies]
  );

  // ---- Manual balance override (feature 12, frontend-only) ----
  const [manualBankBalance, setManualBankBalance] = useState<string>('');
  const [manualCompanyBalance, setManualCompanyBalance] = useState<string>('');
  const bankClosing = useMemo(() => {
    if (manualBankBalance.trim() !== '' && !Number.isNaN(Number(manualBankBalance))) {
      return Number(manualBankBalance);
    }
    return result.bank_net_total?.status === 'found' ? result.bank_net_total.value ?? null : null;
  }, [manualBankBalance, result.bank_net_total]);
  const companyClosing = useMemo(() => {
    if (manualCompanyBalance.trim() !== '' && !Number.isNaN(Number(manualCompanyBalance))) {
      return Number(manualCompanyBalance);
    }
    return result.company_net_total?.status === 'found' ? result.company_net_total.value ?? null : null;
  }, [manualCompanyBalance, result.company_net_total]);

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

  // ---- Discrepancies History drawer (feature 5) ----
  const [discHistoryOpen, setDiscHistoryOpen] = useState(false);

  // ---- View / sort / search / collapse state (features 2,4,6,7) ----
  const [viewMode, setViewMode] = useState<ViewMode>('linear');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortState, setSortState] = useState<Record<string, SortDirection>>({});
  const [collapsedCategories, setCollapsedCategories] = useState<Set<string>>(new Set());

  const handleToggleCollapse = useCallback((category: string) => {
    setCollapsedCategories(prev => {
      const next = new Set(prev);
      if (next.has(category)) next.delete(category);
      else next.add(category);
      return next;
    });
  }, []);

  const handleSortChange = useCallback((category: string) => {
    setSortState(prev => {
      const current = prev[category] ?? 'original';
      const next: SortDirection = current === 'original' ? 'asc' : current === 'asc' ? 'desc' : 'original';
      return { ...prev, [category]: next };
    });
  }, []);

  // Select all items of a category (feature 3)
  const handleSelectAll = useCallback(
    (category: string) => {
      // Recompute the category's current itemIds exactly like CategorizedResults
      // does, so the selected set matches what the checkboxes use. Uses
      // categorizeTransaction so the category key is the enum-form display
      // title, identical to the keys used by sort/collapse state.
      const ids = new Set<string>();
      discrepancies.forEach((d, index) => {
        const c = categorizeTransaction(d.FROM, d['Debit/Credit'], reconciliationType);
        const key = categoryLabel(c, reconciliationType);
        if (key === category) {
          ids.add(generateItemId(d['Transaction_date'], d.FROM, d['Debit/Credit'], index));
        }
      });
      setSelectedItems(prev => {
        const next = new Set(prev);
        let allSelected = true;
        ids.forEach(id => { if (!next.has(id)) allSelected = false; });
        if (allSelected) {
          ids.forEach(id => next.delete(id));
        } else {
          ids.forEach(id => next.add(id));
        }
        return next;
      });
    },
    [discrepancies, reconciliationType]
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Reconciliation Results</h2>
          <p className="text-sm text-muted-foreground">
            Review processing details and unmatched transactions below.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setDiscHistoryOpen(true)}
            disabled={discrepancyHistory.length === 0}
            title={discrepancyHistory.length === 0 ? 'No manual changes made yet' : 'Restore previously reconciled items'}
          >
            <History data-icon="inline-start" />
            Discrepancies History
            {discrepancyHistory.length > 0 && (
              <Badge variant="secondary" className="ml-1">{discrepancyHistory.length}</Badge>
            )}
          </Button>
          <Button variant="outline" size="sm" onClick={handleOpenReconHistory}>
            <RotateCcw data-icon="inline-start" />
            Reconciliation History
          </Button>
          {onStartNew && (
            <Button variant="outline" size="sm" onClick={onStartNew}>
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
            {pdfFileName && (
              <div className="rounded-lg border px-4 py-3" title={pdfFileName}>
                <p className="text-xs text-muted-foreground">Bank Statement (PDF)</p>
                <p className="mt-1 truncate text-sm font-semibold">{pdfFileName}</p>
              </div>
            )}
            {excelFileName && (
              <div className="rounded-lg border px-4 py-3" title={excelFileName}>
                <p className="text-xs text-muted-foreground">Company Data (Excel)</p>
                <p className="mt-1 truncate text-sm font-semibold">{excelFileName}</p>
              </div>
            )}
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
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <CardTitle>Discrepancies</CardTitle>
              <CardDescription>
                Transactions present in one source but not matched in the other
              </CardDescription>
            </div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Undo2 className="size-4" />
              Ctrl+Z undoes the last change
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <CategorizedResults
            discrepancies={discrepancies}
            bankNetTotal={{
              value: bankClosing,
              status: bankClosing !== null ? 'found' : 'missing',
            }}
            companyNetTotal={{
              value: companyClosing,
              status: companyClosing !== null ? 'found' : 'missing',
            }}
            selectedItems={validSelectedItems}
            onToggleSelection={toggleSelection}
            onReconcile={handleReconcile}
            viewMode={viewMode}
            onViewModeChange={setViewMode}
            searchQuery={searchQuery}
            onSearchQueryChange={setSearchQuery}
            sortState={sortState}
            onSortChange={handleSortChange}
            collapsedCategories={collapsedCategories}
            onToggleCollapse={handleToggleCollapse}
            onSelectAll={handleSelectAll}
            onAddManual={handleAddManualDiscrepancy}
          />
        </CardContent>
      </Card>

      {/* Manual balance override (feature 12) — shown near the verdict */}
      <Card>
        <CardHeader>
          <CardTitle>Manual Balances</CardTitle>
          <CardDescription>
            Override or create the closing balances when they could not be retrieved automatically
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <label className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Bank Closing Balance
            </label>
            <Input
              type="number"
              step="0.01"
              placeholder={bankClosing !== null ? formatAmount(bankClosing) : 'Enter bank balance'}
              value={manualBankBalance}
              onChange={(e) => setManualBankBalance(e.target.value)}
            />
            {bankClosing !== null && (
              <p className="text-xs text-muted-foreground">
                Current: {formatAmount(bankClosing)}
              </p>
            )}
          </div>
          <div className="space-y-2">
            <label className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Company Book Balance
            </label>
            <Input
              type="number"
              step="0.01"
              placeholder={companyClosing !== null ? formatAmount(companyClosing) : 'Enter company balance'}
              value={manualCompanyBalance}
              onChange={(e) => setManualCompanyBalance(e.target.value)}
            />
            {companyClosing !== null && (
              <p className="text-xs text-muted-foreground">
                Current: {formatAmount(companyClosing)}
              </p>
            )}
          </div>
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

      {/* ---- Discrepancies History drawer (feature 5) ---- */}
      <Drawer open={discHistoryOpen} onOpenChange={setDiscHistoryOpen}>
        <DrawerContent>
          <DrawerHeader>
            <DrawerTitle>Discrepancies History</DrawerTitle>
            <DrawerDescription>
              Every manual change made to this reconciliation, with the ability to restore each item individually.
            </DrawerDescription>
          </DrawerHeader>
          <div className="space-y-4 overflow-y-auto px-4 pb-6">
            {discrepancyHistory.length === 0 ? (
              <p className="py-8 text-center text-sm text-muted-foreground">
                No manual changes yet. Select items and reconcile to build history.
              </p>
            ) : (
              discrepancyHistory.map(entry => (
                <div key={entry.id} className="rounded-lg border p-3">
                  <div className="flex items-center justify-between gap-2">
                    <div className="min-w-0">
                      <p className="text-sm font-semibold">{entry.action}</p>
                      <p className="text-xs text-muted-foreground">
                        {new Date(entry.timestamp).toLocaleString('en-US', {
                          dateStyle: 'medium',
                          timeStyle: 'short',
                        })}
                        {' · '}{entry.items.length} item{entry.items.length === 1 ? '' : 's'}
                      </p>
                    </div>
                  </div>
                  <div className="mt-3 space-y-2">
                    {entry.items.map(item => (
                      <div
                        key={item.discrepancy_id ?? `${item['Transaction_date']}-${item['Transaction Detail']}-${item['Debit/Credit']}`}
                        className="flex items-center justify-between gap-3 rounded-md border bg-muted/30 px-3 py-2 text-sm"
                      >
                        <div className="min-w-0">
                          <p className="truncate font-medium">{item['Transaction Detail']}</p>
                          <p className="text-xs text-muted-foreground">
                            {item['Transaction_date']} · {item.FROM}
                            {item.from_past ? ' · From Past' : ''}
                          </p>
                        </div>
                        <div className="flex shrink-0 items-center gap-2">
                          <span className="font-mono text-sm">{formatAmount(item['Debit/Credit'])}</span>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleRestoreItems(entry.id, [item])}
                          >
                            Restore
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))
            )}
          </div>
          <DrawerFooter>
            <DrawerClose
              render={<Button variant="outline" />}
            >
              Close
            </DrawerClose>
          </DrawerFooter>
        </DrawerContent>
      </Drawer>

      {/* ---- Past Reconciliations drawer (shared with the upload pages) ---- */}
      {reconHistoryError && (
        <div className="mb-3 flex items-center gap-2 rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2 text-xs text-destructive">
          {reconHistoryError}
        </div>
      )}
      <PastReconciliationsDrawer
        open={reconHistoryOpen}
        onOpenChange={(next) => {
          setReconHistoryOpen(next);
          if (!next) setReconHistoryError(null);
        }}
        onLoadFile={(fileName) => {
          void handleLoadPastFile(fileName);
        }}
      />

    </div>
  );
}

// وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
