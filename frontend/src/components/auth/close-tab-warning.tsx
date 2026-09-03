/* بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */
/**
 * CloseTabWarning (feature 008, feature 1) — a global beforeunload guard.
 *
 * Mounted once in the root layout so closing / reloading the tab always shows
 * the browser's "Leave site?" popup, regardless of whether the user is on the
 * home page, mid AI processing, or viewing the final reconciliation list.
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
