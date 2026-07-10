/**
 # بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
 * Manual Reconciliation Component for Reconciliation Frontend Enhancements
 * Feature: 001-reconciliation-frontend-features
 *
 * This component provides manual reconciliation capabilities allowing users to
 * select specific discrepancy items for removal with real-time calculation preview.
 */

'use client';

import { useMemo, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  CategorizedTransaction,
  ReconciliationCalculation
} from '@/types/categorization.types';
import { calculateReconciliationPreview } from '@/lib/utils/calculationUtils';

interface ManualReconciliationProps {
  transactions: CategorizedTransaction[];
  selectedItems?: Set<string>;
  onToggleSelection?: (itemId: string) => void;
  onReconcile?: (selectedItemIds: Set<string>) => void;
}

/**
 * وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
 * Manual reconciliation component with selection tracking and calculation preview
 */
export function ManualReconciliation({ transactions, selectedItems = new Set(), onToggleSelection, onReconcile }: ManualReconciliationProps) {
  // Derived state: categorized transactions by category
  const categorizedTransactions = useMemo(() => {
    const grouped: { [key: string]: CategorizedTransaction[] } = {
      'UNPRESENTED CHECKS': [],
      'UNCLEARED CHECKS': [],
      'BANK DEBITED BUT NOT CREDITED IN CASH BOOK': [],
      'BANK CREDITED BUT NOT DEBITED IN CASH BOOK': []
    };

    transactions.forEach(t => {
      grouped[t.category].push(t);
    });

    return grouped;
  }, [transactions]);

  // Derived state: reconciliation calculation preview
  const calculation: ReconciliationCalculation = useMemo(() => {
    return calculateReconciliationPreview(selectedItems, transactions);
  }, [selectedItems, transactions]);

  // Clear all selections
  const handleClearSelections = useCallback(() => {
    // Toggle off each selected item
    selectedItems.forEach(itemId => {
      onToggleSelection?.(itemId);
    });
  }, [selectedItems, onToggleSelection]);

  // Execute manual reconciliation
  const handleExecuteReconciliation = useCallback(() => {
    if (calculation.itemCount === 0) return;

    // Warn if not net-zero
    if (!calculation.isNetZero && calculation.itemCount > 0) {
      const confirmed = window.confirm(
        `Warning: Selected items do not sum to zero (${calculation.summary}). ` +
        `This may indicate an incomplete reconciliation. Continue?`
      );
      if (!confirmed) return;
    }

    // Execute reconciliation callback
    if (onReconcile) {
      onReconcile(selectedItems);
    }
  }, [calculation, onReconcile, selectedItems]);

  const isButtonDisabled = calculation.itemCount === 0;
  const hasSelections = calculation.itemCount > 0;

  return (
    <div className="space-y-4 mt-6">
      {/* Calculation Preview Section */}
      {hasSelections && (
        <div className="rounded-lg border bg-muted/30 p-4 space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-semibold">Manual Reconciliation Preview</h4>
            <Badge variant="secondary" className="bg-blue-100 text-blue-800">
              {calculation.itemCount} items selected
            </Badge>
          </div>

          <div className="grid gap-3 sm:grid-cols-3">
            <div className="rounded border bg-background p-3">
              <p className="text-xs text-muted-foreground">Total Amount</p>
              <p className={`mt-1 text-lg font-semibold ${
                calculation.totalAmount >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {calculation.totalAmount.toLocaleString('en-US', {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </p>
            </div>

            <div className="rounded border bg-background p-3">
              <p className="text-xs text-muted-foreground">Status</p>
              <p className="mt-1 text-sm font-medium">
                {calculation.isNetZero ? (
                  <span className="text-green-600">✓ Net Zero</span>
                ) : (
                  <span className="text-orange-600">⚠️ Imbalance</span>
                )}
              </p>
            </div>

            <div className="rounded border bg-background p-3">
              <p className="text-xs text-muted-foreground">Summary</p>
              <p className="mt-1 text-sm">{calculation.summary}</p>
            </div>
          </div>

          {/* Clear Selections Button */}
          <Button
            variant="outline"
            size="sm"
            onClick={handleClearSelections}
            className="w-full"
          >
            Clear Selections
          </Button>
        </div>
      )}

      {/* Manual Reconciliation Button */}
      <div className="flex items-center gap-4">
        <Button
          onClick={handleExecuteReconciliation}
          disabled={isButtonDisabled}
          size="lg"
          className="w-full sm:w-auto"
        >
          <span className="mr-2">
            {isButtonDisabled ? 'Select items to reconcile' : 'Execute Manual Reconciliation'}
          </span>
          {!isButtonDisabled && (
            <Badge variant="secondary" className="ml-2 bg-blue-100 text-blue-800">
              {calculation.itemCount}
            </Badge>
          )}
        </Button>
      </div>

      {/* Selection Summary by Category */}
      {hasSelections && (
        <div className="rounded-lg border bg-muted/30 p-4">
          <h4 className="text-sm font-semibold mb-3">Selection Summary by Category</h4>
          <div className="space-y-2">
            {Object.entries(categorizedTransactions).map(([category, items]) => {
              const selectedInCategory = items.filter(t => selectedItems.has(t.itemId));
              const selectedCount = selectedInCategory.length;

              if (selectedCount === 0) return null;

              return (
                <div key={category} className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">{category}:</span>
                  <Badge variant="outline" className="font-mono">
                    {selectedCount} / {items.length}
                  </Badge>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

// وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ