/* بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */
/**
 * useHistoryState — a generic undo stack hook (feature 008, undo feature 5).
 *
 * Wraps a useState value with a `past` stack. `push(next)` snapshots the
 * current value onto the stack before applying the next one; `undo()` pops
 * the most recent snapshot. Used by ReconciliationResults to make every
 * discrepancy mutation (manual reconcile, advisor reconcile, manual add,
 * restore) undoable with ctrl+z.
 */

'use client';

import { useCallback, useRef, useState } from 'react';

const MAX_UNDO_DEPTH = 100;

export function useHistoryState<T>(initial: T) {
  const [present, setPresentState] = useState<T>(initial);
  // Ref, not state: the undo stack never needs to re-render on its own.
  const pastRef = useRef<T[]>([]);

  /** Set the next value, snapshotting the current one onto the undo stack. */
  const push = useCallback((next: T | ((prev: T) => T)) => {
    setPresentState((prev) => {
      const resolved =
        typeof next === 'function' ? (next as (p: T) => T)(prev) : next;
      if (resolved === prev) return prev;
      pastRef.current = [...pastRef.current.slice(-(MAX_UNDO_DEPTH - 1)), prev];
      return resolved;
    });
  }, []);

  /** Pop the most recent snapshot. Returns true if an undo happened. */
  const undo = useCallback((): boolean => {
    const past = pastRef.current;
    if (past.length === 0) return false;
    const previous = past[past.length - 1];
    pastRef.current = past.slice(0, -1);
    setPresentState(previous);
    return true;
  }, []);

  /** Clear the undo stack (e.g. on a fresh reconciliation). */
  const resetHistory = useCallback(() => {
    pastRef.current = [];
  }, []);

  const canUndo = useCallback(() => pastRef.current.length > 0, []);

  return { present, push, undo, resetHistory, canUndo };
}

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
