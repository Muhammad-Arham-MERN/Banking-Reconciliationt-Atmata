'use client';

/** بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */
/**
 * Dummy Results Viewer — renders the generated dummy reconciliation through
 * the exact same ReconciliationResults component the real flow uses, so the
 * display (categories, columns, verification panel, advisor panel/chat) is
 * byte-for-byte identical to a real run. A "Regenerate" button produces a
 * fresh seeded batch on demand.
 */

import { useState } from 'react';
import { ReconciliationResults } from '@/components/results/ReconciliationResults';
import { generateDummyReconciliation } from '@/lib/utils/dummyReconciliationData';
import { Button } from '@/components/ui/button';
import { RefreshCw, TestTube } from 'lucide-react';

export function DummyResultsViewer() {
  const [result, setResult] = useState(() => generateDummyReconciliation());

  const handleRegenerate = () => {
    setResult(generateDummyReconciliation());
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="w-full max-w-6xl mx-auto space-y-4">
      <div className="flex justify-center">
        <Button variant="outline" onClick={handleRegenerate}>
          <RefreshCw data-icon="inline-start" />
          Regenerate Dummy Data
        </Button>
      </div>

      <ReconciliationResults
        result={result}
        pdfFileName="dummy-bank-statement.pdf"
        excelFileName="dummy-company-records.xlsx"
      />
    </div>
  );
}

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
