/* بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */
/**
 * CloseTabWarning — a beforeunload guard for the AI reconciliation page.
 *
 * Mounted on /upload-ai so closing / reloading the tab shows the browser's
 * native "Leave site?" confirmation, preventing an accidental close from
 * discarding an in-progress reconciliation.
 */

'use client';

import { useEffect } from 'react';

export function CloseTabWarning() {
  useEffect(() => {
    const handleBeforeUnload = (event: BeforeUnloadEvent) => {
      // Standard cross-browser pattern: preventDefault + returnValue makes the
      // browser show its native "Leave site?" confirmation dialog.
      event.preventDefault();
      event.returnValue = '';
      return '';
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, []);

  return null;
}

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
