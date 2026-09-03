/**
 # بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
 * Categorized Results Component for Reconciliation Frontend Enhancements
 * Feature: 001-reconciliation-frontend-features (+ feature 008 UX upgrades:
 * collapsible categories, select-all, search, sort, grid/linear view,
 * manual discrepancy addition, sticky list header).
 *
 * This component displays unreconciled transactions automatically categorized into
 * four accounting-specific sections based on transaction source and value polarity.
 */

'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { DiscrepancyTransaction, NetTotalValue } from '@/types/reconciliation.types';
import { ManualReconciliation } from '@/components/results/ManualReconciliation';
import {
  TransactionCategory,
  CategorizedTransaction,
  ViewMode,
  SortDirection,
  ManualDiscrepancyDraft,
} from '@/types/categorization.types';
import {
  categorizeTransaction,
  generateItemId,
  getDisplayAmount,
  formatAmount,
  categoryLabel,
} from '@/lib/utils/categorizationUtils';
import { useReconciliationType } from '@/components/providers/reconciliation-type-provider';
import { CheckCircle2, XCircle, AlertTriangle, ChevronDown, ChevronRight, Plus, Search, LayoutGrid, List } from 'lucide-react';
import { Collapsible, CollapsibleTrigger, CollapsibleContent } from '@/components/ui/collapsible';
import { Popover, PopoverContent, PopoverTrigger, PopoverHeader, PopoverTitle, PopoverDescription } from '@/components/ui/popover';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Button } from '@/components/ui/button';

interface CategorizedResultsProps {
  discrepancies: DiscrepancyTransaction[];
  bankNetTotal?: NetTotalValue;
  companyNetTotal?: NetTotalValue;
  selectedItems?: Set<string>;
  onToggleSelection?: (itemId: string) => void;
  onReconcile?: (selectedItemIds: Set<string>) => void;
  // ---- feature 008 props ----
  viewMode?: ViewMode;
  onViewModeChange?: (mode: ViewMode) => void;
  searchQuery?: string;
  onSearchQueryChange?: (q: string) => void;
  sortState?: Record<string, SortDirection>;
  onSortChange?: (category: string) => void;
  collapsedCategories?: Set<string>;
  onToggleCollapse?: (category: string) => void;
  onSelectAll?: (category: string) => void;
  onAddManual?: (category: string, draft: ManualDiscrepancyDraft) => void;
}

const SORT_LABELS: Record<SortDirection, string> = {
  original: 'Original',
  asc: 'Lowest → Highest',
  desc: 'Highest → Lowest',
};

/**
 * وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
 * Main categorization results component
 */
export function CategorizedResults({
  discrepancies,
  bankNetTotal,
  companyNetTotal,
  selectedItems,
  onToggleSelection,
  onReconcile,
  viewMode = 'linear',
  onViewModeChange,
  searchQuery = '',
  onSearchQueryChange,
  sortState = {},
  onSortChange,
  collapsedCategories = new Set<string>(),
  onToggleCollapse,
  onSelectAll,
  onAddManual,
}: CategorizedResultsProps) {
  const { reconciliationType } = useReconciliationType();

  // Memoized categorization of transactions
  const categorizedData = useMemo(() => {
    return discrepancies.map((d, index) => {
      const category = categorizeTransaction(d.FROM, d['Debit/Credit'], reconciliationType);
      const itemId = generateItemId(d['Transaction_date'], d.FROM, d['Debit/Credit'], index);
      const displayAmount = getDisplayAmount(d.FROM, d['Debit/Credit'], category, reconciliationType);

      return {
        ...d,
        category,
        itemId,
        displayAmount,
        displayValue: formatAmount(displayAmount),
      };
    });
  }, [discrepancies, reconciliationType]);

  // Group transactions by the four display categories. In vendor mode the
  // Bank-side categories are replaced by the vendor categories (same slots).
  const displayDebited = reconciliationType === 'vendor'
    ? TransactionCategory.VENDOR_DEBITED_NOT_CREDITED
    : TransactionCategory.BANK_DEBITED_NOT_CREDITED;
  const displayCredited = reconciliationType === 'vendor'
    ? TransactionCategory.VENDOR_CREDITED_NOT_DEBITED
    : TransactionCategory.BANK_CREDITED_NOT_DEBITED;

  const categories = useMemo(() => {
    const grouped: { [key in TransactionCategory]: CategorizedTransaction[] } = {
      [TransactionCategory.UNPRESENTED_CHECKS]: [],
      [TransactionCategory.UNCLEARED_CHECKS]: [],
      [TransactionCategory.BANK_DEBITED_NOT_CREDITED]: [],
      [TransactionCategory.BANK_CREDITED_NOT_DEBITED]: [],
      [TransactionCategory.VENDOR_DEBITED_NOT_CREDITED]: [],
      [TransactionCategory.VENDOR_CREDITED_NOT_DEBITED]: []
    };

    categorizedData.forEach(transaction => {
      grouped[transaction.category].push(transaction);
    });

    return grouped;
  }, [categorizedData]);

  // Display order: company categories first, then the source-side (bank/vendor)
  // credited + debited slots — matches the pre-008 visual order exactly.
  // Labels are the enum-form display titles ("UNPRESENTED CHECKS", etc.) and
  // double as the stable keys for sort/collapse/select-all state.
  const displayOrder = useMemo(
    () => [
      { key: TransactionCategory.UNPRESENTED_CHECKS, label: categoryLabel(TransactionCategory.UNPRESENTED_CHECKS, reconciliationType) },
      { key: TransactionCategory.UNCLEARED_CHECKS, label: categoryLabel(TransactionCategory.UNCLEARED_CHECKS, reconciliationType) },
      { key: displayCredited, label: categoryLabel(displayCredited, reconciliationType) },
      { key: displayDebited, label: categoryLabel(displayDebited, reconciliationType) },
    ],
    [displayCredited, displayDebited, reconciliationType]
  );

  // ---- feature 008: live search filtering (feature 4) ----
  const normalizedQuery = searchQuery.trim().toLowerCase();

  const filteredCategories = useMemo(() => {
    if (!normalizedQuery) return categories;
    const filtered: { [key in TransactionCategory]: CategorizedTransaction[] } = {
      [TransactionCategory.UNPRESENTED_CHECKS]: [],
      [TransactionCategory.UNCLEARED_CHECKS]: [],
      [TransactionCategory.BANK_DEBITED_NOT_CREDITED]: [],
      [TransactionCategory.BANK_CREDITED_NOT_DEBITED]: [],
      [TransactionCategory.VENDOR_DEBITED_NOT_CREDITED]: [],
      [TransactionCategory.VENDOR_CREDITED_NOT_DEBITED]: []
    };
    for (const cat of Object.keys(categories) as TransactionCategory[]) {
      filtered[cat] = categories[cat].filter(t =>
        t['Transaction Detail'].toLowerCase().includes(normalizedQuery) ||
        t['Transaction_date'].toLowerCase().includes(normalizedQuery) ||
        formatAmount(t.displayAmount).toLowerCase().includes(normalizedQuery) ||
        String(t.displayAmount).includes(normalizedQuery)
      );
    }
    return filtered;
  }, [categories, normalizedQuery]);

  // ---- feature 008: per-category sort (feature 7) ----
  const sortedCategories = useMemo(() => {
    const sorted: { [key in TransactionCategory]: CategorizedTransaction[] } = {
      [TransactionCategory.UNPRESENTED_CHECKS]: [],
      [TransactionCategory.UNCLEARED_CHECKS]: [],
      [TransactionCategory.BANK_DEBITED_NOT_CREDITED]: [],
      [TransactionCategory.BANK_CREDITED_NOT_DEBITED]: [],
      [TransactionCategory.VENDOR_DEBITED_NOT_CREDITED]: [],
      [TransactionCategory.VENDOR_CREDITED_NOT_DEBITED]: []
    };
    for (const cat of Object.keys(filteredCategories) as TransactionCategory[]) {
      const dir = sortState[categoryLabel(cat, reconciliationType)] ?? 'original';
      const list = filteredCategories[cat];
      if (dir === 'original') {
        sorted[cat] = list;
      } else {
        const sortedList = [...list].sort((a, b) =>
          dir === 'asc' ? a.displayAmount - b.displayAmount : b.displayAmount - a.displayAmount
        );
        sorted[cat] = sortedList;
      }
    }
    return sorted;
  }, [filteredCategories, sortState, reconciliationType]);

  // Use the sorted view for everything below.
  const viewCategories = sortedCategories;

  const categorySubtotals = useMemo(() => {
    const subtotals: Record<string, { total: number; count: number }> = {};
    for (const [category, txs] of Object.entries(viewCategories)) {
      const total = txs.reduce((sum, t) => sum + t.displayAmount, 0);
      subtotals[category] = { total, count: txs.length };
    }
    return subtotals;
  }, [viewCategories]);

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

  const totalCount = useMemo(
    () => displayOrder.reduce((sum, { key }) => sum + viewCategories[key].length, 0),
    [displayOrder, viewCategories]
  );

  const renderCategorySection = (cat: { key: TransactionCategory; label: string }) => (
    <CategorySection
      key={cat.label}
      title={cat.label}
      transactions={viewCategories[cat.key]}
      count={viewCategories[cat.key].length}
      allCount={categories[cat.key].length}
      isSearching={normalizedQuery.length > 0}
      selectedItems={selectedItems}
      onToggleSelection={onToggleSelection}
      collapsed={collapsedCategories.has(cat.label)}
      onToggleCollapse={() => onToggleCollapse?.(cat.label)}
      sortDirection={sortState[cat.label] ?? 'original'}
      onSort={() => onSortChange?.(cat.label)}
      onSelectAll={() => onSelectAll?.(cat.label)}
      onAddManual={(draft) => onAddManual?.(cat.label, draft)}
    />
  );

  return (
    <div className="space-y-6">
      {/* ---- feature 008 sticky list header (feature 11) ----
          Hides on scroll up, shows on scroll down; carries the search box and
          the Linear/Grid view switch. */}
      <StickyListHeader
        searchQuery={searchQuery}
        onSearchQueryChange={onSearchQueryChange ?? (() => {})}
        viewMode={viewMode}
        onViewModeChange={onViewModeChange ?? (() => {})}
        totalCount={totalCount}
      />

      <div className="flex flex-wrap items-start justify-between gap-3">
        <p className="text-sm text-muted-foreground pt-2">
          Found <span className="font-semibold text-foreground">{totalCount}</span> transactions
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

      {/* ---- feature 008 grid/linear layout (feature 6) ---- */}
      {viewMode === 'grid' ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 items-start">
          {displayOrder.map(cat => renderCategorySection(cat))}
        </div>
      ) : (
        <div className="space-y-6">
          {displayOrder.map(cat => renderCategorySection(cat))}
        </div>
      )}

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
          {displayOrder.map(({ key, label }) => {
            const { total, count } = categorySubtotals[key] ?? { total: 0, count: 0 };
            return count > 0 && (
              <div key={key} className="rounded border bg-background px-3 py-2 text-xs">
                <p className="font-medium text-muted-foreground truncate" title={label}>
                  {label.length > 30 ? label.slice(0, 30) + '…' : label}
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
            );
          })}
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

// Helper: build the sticky header scroll listener without extra re-renders.
function useScrollListener(handler: () => void) {
  const handlerRef = useRef(handler);
  handlerRef.current = handler;
  useEffect(() => {
    const onScroll = () => handlerRef.current();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);
}

/**
 * Sticky list header (feature 11): hides when scrolling up, shows when
 * scrolling down. Carries the search box and Linear/Grid view switch.
 */
function StickyListHeader({
  searchQuery,
  onSearchQueryChange,
  viewMode,
  onViewModeChange,
  totalCount,
}: {
  searchQuery: string;
  onSearchQueryChange: (q: string) => void;
  viewMode: ViewMode;
  onViewModeChange: (mode: ViewMode) => void;
  totalCount: number;
}) {
  const [visible, setVisible] = useState(true);
  const lastScrollYRef = useRef(0);

  const handleScroll = () => {
    const currentY = window.scrollY;
    if (currentY < 80) {
      setVisible(true);
    } else if (currentY > lastScrollYRef.current + 8) {
      setVisible(false);
    } else if (currentY < lastScrollYRef.current - 8) {
      setVisible(true);
    }
    lastScrollYRef.current = currentY;
  };

  useScrollListener(handleScroll);

  return (
    <div
      className={`sticky top-0 z-30 rounded-lg border bg-background/95 px-4 py-3 shadow-sm backdrop-blur transition-transform duration-200 ${
        visible ? 'translate-y-0' : '-translate-y-[110%]'
      }`}
    >
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative min-w-[200px] flex-1">
          <Search className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            type="search"
            placeholder="Search discrepancies…"
            value={searchQuery}
            onChange={(e) => onSearchQueryChange(e.target.value)}
            className="pl-8"
          />
        </div>
        <div className="flex items-center gap-1 rounded-lg border bg-muted/30 p-0.5">
          <Button
            variant={viewMode === 'linear' ? 'default' : 'ghost'}
            size="sm"
            onClick={() => onViewModeChange('linear')}
            className="gap-1.5"
          >
            <List data-icon="inline-start" />
            Linear
          </Button>
          <Button
            variant={viewMode === 'grid' ? 'default' : 'ghost'}
            size="sm"
            onClick={() => onViewModeChange('grid')}
            className="gap-1.5"
          >
            <LayoutGrid data-icon="inline-start" />
            Grid
          </Button>
        </div>
        <span className="text-xs text-muted-foreground">
          {totalCount} shown
        </span>
      </div>
    </div>
  );
}

/**
 * Category Section component for displaying a single category of transactions
 * Reuses existing table design patterns from DiscrepancyList component.
 * Feature 008: collapsible (arrow), select-all, amount sort, manual "+" add.
 */
interface CategorySectionProps {
  title: string;
  transactions: CategorizedTransaction[];
  count: number;
  /** Total items in the category before search filtering */
  allCount: number;
  /** True when a live search is active (for the empty-state message) */
  isSearching: boolean;
  selectedItems?: Set<string>;
  onToggleSelection?: (itemId: string) => void;
  collapsed?: boolean;
  onToggleCollapse?: () => void;
  sortDirection?: SortDirection;
  onSort?: () => void;
  onSelectAll?: () => void;
  onAddManual?: (draft: ManualDiscrepancyDraft) => void;
}

function CategorySection({
  title,
  transactions,
  count,
  allCount,
  isSearching,
  selectedItems,
  onToggleSelection,
  collapsed = false,
  onToggleCollapse,
  sortDirection = 'original',
  onSort,
  onSelectAll,
  onAddManual,
}: CategorySectionProps) {
  const [addOpen, setAddOpen] = useState(false);
  const [draft, setDraft] = useState<ManualDiscrepancyDraft>({
    date: new Date().toISOString().slice(0, 10),
    details: '',
    amount: 0,
    fromPast: false,
  });

  const selectedCount = useMemo(
    () => transactions.filter(t => selectedItems?.has(t.itemId)).length,
    [transactions, selectedItems]
  );

  const handleSubmitManual = () => {
    if (!draft.details.trim()) return;
    onAddManual?.({ ...draft, amount: Number(draft.amount) || 0 });
    setAddOpen(false);
    setDraft({ date: new Date().toISOString().slice(0, 10), details: '', amount: 0, fromPast: false });
  };

  return (
    <Collapsible open={!collapsed} onOpenChange={(open) => onToggleCollapse?.()}>
      <div className="rounded-lg border">
        {/* Category header: arrow (collapse), title, count, select-all, sort */}
        <div className="flex items-center justify-between gap-2 px-4 py-3 bg-muted/40 border-b">
          <div className="flex items-center gap-2 min-w-0">
            <CollapsibleTrigger
              render={
                <button
                  type="button"
                  className="flex items-center gap-1 rounded-md p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
                  aria-label={collapsed ? `Expand ${title}` : `Collapse ${title}`}
                />
              }
            >
              {collapsed ? (
                <ChevronRight className="size-4" />
              ) : (
                <ChevronDown className="size-4" />
              )}
            </CollapsibleTrigger>
            <h3 className="truncate text-sm font-semibold" title={title}>{title}</h3>
            <span className="shrink-0 text-xs text-muted-foreground bg-background px-2 py-1 rounded">
              {count} {count === 1 ? 'transaction' : 'transactions'}
              {count !== allCount ? ` of ${allCount}` : ''}
            </span>
          </div>

          <div className="flex items-center gap-1 shrink-0">
            {onSelectAll && count > 0 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onSelectAll}
                className="gap-1 text-xs"
                title={selectedCount === count ? 'Deselect all' : 'Select all items in this category'}
              >
                <input
                  type="checkbox"
                  checked={selectedCount === count && count > 0}
                  readOnly
                  className="pointer-events-none size-3.5 rounded border-gray-300 text-blue-600"
                />
                Select all
              </Button>
            )}
            {onAddManual && (
              <Popover open={addOpen} onOpenChange={setAddOpen}>
                <PopoverTrigger
                  render={
                    <Button
                      variant="ghost"
                      size="sm"
                      className="gap-1 text-xs"
                      title={`Add a manual discrepancy to ${title}`}
                    />
                  }
                >
                  <Plus className="size-4" />
                  Add
                </PopoverTrigger>
                <PopoverContent align="end" className="w-80">
                  <PopoverHeader>
                    <PopoverTitle>Add manual discrepancy</PopoverTitle>
                    <PopoverDescription>
                      Creates an entry inside {title}
                    </PopoverDescription>
                  </PopoverHeader>
                  <div className="space-y-2.5 px-0.5">
                    <div className="space-y-1.5">
                      <label className="text-xs font-medium text-muted-foreground">Date</label>
                      <Input
                        type="date"
                        value={draft.date}
                        onChange={(e) => setDraft(d => ({ ...d, date: e.target.value }))}
                      />
                    </div>
                    <div className="space-y-1.5">
                      <label className="text-xs font-medium text-muted-foreground">Details</label>
                      <Textarea
                        placeholder="Transaction details"
                        value={draft.details}
                        onChange={(e) => setDraft(d => ({ ...d, details: e.target.value }))}
                      />
                    </div>
                    <div className="space-y-1.5">
                      <label className="text-xs font-medium text-muted-foreground">Amount</label>
                      <Input
                        type="number"
                        step="0.01"
                        placeholder="0.00"
                        value={draft.amount === 0 ? '' : String(draft.amount)}
                        onChange={(e) => setDraft(d => ({ ...d, amount: Number(e.target.value) }))}
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <label className="text-xs font-medium text-muted-foreground">From Past</label>
                      <Switch
                        checked={draft.fromPast}
                        onCheckedChange={(checked) => setDraft(d => ({ ...d, fromPast: checked }))}
                      />
                    </div>
                  </div>
                  <div className="mt-3 flex justify-end">
                    <Button size="sm" onClick={handleSubmitManual} disabled={!draft.details.trim()}>
                      Done
                    </Button>
                  </div>
                </PopoverContent>
              </Popover>
            )}
          </div>
        </div>

        <CollapsibleContent>
          {/* Column headers */}
          <div className="flex items-center px-4 py-2 text-xs font-medium text-muted-foreground border-b bg-muted/20">
            {onToggleSelection && <div className="w-[40px]" />}
            <div className="flex-[180px]">Date</div>
            <div className="flex-[300px]">Details</div>
            {/* Amount header doubles as the sort toggle (feature 7) */}
            <button
              type="button"
              onClick={onSort}
              className="flex w-[130px] items-center justify-end gap-1 text-right font-medium text-muted-foreground hover:text-foreground"
              title={`Sort by amount — ${SORT_LABELS[sortDirection]}`}
            >
              Amount
              <ChevronDown
                className={`size-3 transition-transform ${
                  sortDirection === 'desc' ? 'rotate-180' : sortDirection === 'asc' ? 'rotate-0' : 'opacity-40'
                }`}
              />
            </button>
            <div className="w-[100px] text-center">Source</div>
            <div className="w-[90px] text-center">From Past</div>
          </div>

          {count === 0 ? (
            <div className="px-4 py-6 text-center">
              <p className="text-sm font-medium text-green-800">
                {isSearching
                  ? 'No transactions match your search in this category'
                  : `${title}: No transactions in this category`}
              </p>
            </div>
          ) : (
            <div className="divide-y">
              {transactions.map((transaction) => (
                <div
                  key={transaction.itemId}
                  className={`flex items-center px-4 py-3 hover:bg-muted/30 ${
                    selectedItems?.has(transaction.itemId) ? 'bg-blue-50/50 dark:bg-blue-950/30' : ''
                  } ${
                    transaction.from_past ? 'bg-purple-50 dark:bg-purple-950/30' : ''
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
          )}
        </CollapsibleContent>
      </div>
    </Collapsible>
  );
}

// وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
