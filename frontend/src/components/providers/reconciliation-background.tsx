/* بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */
/**
 * Reconciliation Background
 * Client wrapper that tints the page background slightly based on the active
 * reconciliation mode. Bank keeps the indigo/violet gradient; Vendor shifts
 * to a warm amber tint - in both light and dark themes - so the two modes
 * are visually distinguishable at a glance.
 */
'use client';

import { ReactNode } from 'react';
import { useReconciliationType } from './reconciliation-type-provider';

export function ReconciliationBackground({ children }: { children: ReactNode }) {
  const { reconciliationType } = useReconciliationType();
  const vendor = reconciliationType === 'vendor';

  return (
    <div
      className={`min-h-screen transition-colors duration-500 ${
        vendor
          ? 'bg-gradient-to-br from-amber-50 via-orange-50/40 to-amber-100/60 dark:from-gray-950 dark:via-gray-900 dark:to-amber-950/30'
          : 'bg-gradient-to-br from-indigo-50 to-violet-50 dark:from-gray-950 dark:to-gray-900'
      }`}
    >
      {children}
    </div>
  );
}

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
