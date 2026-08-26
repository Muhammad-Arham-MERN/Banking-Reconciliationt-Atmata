/* بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */
/**
 * Reconciliation Type Provider
 * Holds the active reconciliation mode ("bank" | "vendor") in a client
 * context so the page background, the upload form, and the results view can
 * all react to the same selection without prop-drilling.
 */
'use client';

import { createContext, useContext, useState, ReactNode } from 'react';

export type ReconciliationType = 'bank' | 'vendor';

interface ReconciliationTypeContextValue {
  reconciliationType: ReconciliationType;
  setReconciliationType: (t: ReconciliationType) => void;
}

const ReconciliationTypeContext = createContext<ReconciliationTypeContextValue>({
  reconciliationType: 'bank',
  setReconciliationType: () => {},
});

export function ReconciliationTypeProvider({ children }: { children: ReactNode }) {
  const [reconciliationType, setReconciliationType] = useState<ReconciliationType>('bank');
  return (
    <ReconciliationTypeContext.Provider value={{ reconciliationType, setReconciliationType }}>
      {children}
    </ReconciliationTypeContext.Provider>
  );
}

export function useReconciliationType() {
  return useContext(ReconciliationTypeContext);
}

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
