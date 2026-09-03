/* بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */

/**
 * EditableDiscrepancyRow
 *
 * One discrepancy row inside the past-file editor. Shows Date / Details /
 * Amount as static text with an edit (pencil) and delete (trash) action.
 * Clicking the pencil turns the fields into inputs pre-filled with the current
 * values; the row auto-saves on blur (or Enter), and the trash triggers a
 * two-step inline confirm. Amount is edited as an UNSIGNED value — the stored
 * signed value is derived from the category's sign convention on save.
 */
'use client';

import React, { useRef, useState } from 'react';
import { Pencil, Trash2, Check, X } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface EditableDiscrepancyRowProps {
  /** Row index shown at the left (1-based). */
  index: number;
  /** Category label — drives the sign applied to the stored amount. */
  category: string;
  /** True when this is the "new row" placeholder (no data yet). */
  isNew?: boolean;
  date: string;
  details: string;
  /** Signed stored amount (wire value). */
  amount: number;
  /** Whether this row is currently in edit mode (controlled by parent for "new" rows). */
  editing?: boolean;
  onEditingChange?: (editing: boolean) => void;
  /** Called with the UPDATED entry when the row auto-saves. */
  onSave: (entry: { date: string; details: string; amount: number }) => void;
  /** Called when the user confirms deletion. */
  onDelete?: () => void;
  /** Called when the user cancels an in-progress edit (Escape / X). */
  onCancelEdit?: () => void;
}

/** Map a category label to its settled sign (mirrors the backend). */
export function signForCategory(category: string): number {
  const c = category.trim().toLowerCase();
  if (
    c === 'unpresented checks' ||
    c.includes('debited') ||
    (c.includes('credited') && !c.includes('not debited'))
  ) {
    return -1;
  }
  return 1;
}

export function EditableDiscrepancyRow({
  index,
  category,
  isNew = false,
  date: initialDate,
  details: initialDetails,
  amount,
  editing = false,
  onEditingChange,
  onSave,
  onDelete,
  onCancelEdit,
}: EditableDiscrepancyRowProps) {
  const [dateDraft, setDateDraft] = useState(initialDate);
  const [detailsDraft, setDetailsDraft] = useState(initialDetails);
  const [amountDraft, setAmountDraft] = useState(
    isNew ? '' : String(Math.abs(amount))
  );
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const rowRef = useRef<HTMLDivElement>(null);

  // When the parent flips editing on (e.g. the "+" row), seed drafts fresh.
  // Done during render so the inputs show the current values immediately.
  const [seededEditing, setSeededEditing] = useState(false);
  if (editing && !seededEditing) {
    setSeededEditing(true);
    setDateDraft(initialDate);
    setDetailsDraft(initialDetails);
    setAmountDraft(isNew ? '' : String(Math.abs(amount)));
    setError(null);
    setConfirmDelete(false);
  }
  if (!editing && seededEditing) {
    setSeededEditing(false);
  }

  const commit = () => {
    const parsed = parseFloat(amountDraft.replace(/,/g, ''));
    if (Number.isNaN(parsed)) {
      setError('Enter a valid amount (e.g. 49000 or 49,000).');
      return;
    }
    const signed = parsed * signForCategory(category);
    onSave({
      date: dateDraft.trim(),
      details: detailsDraft.trim(),
      amount: signed,
    });
    setError(null);
    if (onEditingChange) onEditingChange(false);
  };

  const cancel = () => {
    setDateDraft(initialDate);
    setDetailsDraft(initialDetails);
    setAmountDraft(isNew ? '' : String(Math.abs(amount)));
    setError(null);
    setConfirmDelete(false);
    if (onCancelEdit) onCancelEdit();
    if (onEditingChange) onEditingChange(false);
  };

  // Commit only when focus leaves the ENTIRE row — moving between the row's
  // own inputs (date -> details -> amount) must NOT save, while clicking any
  // part outside the row (another row, the section header, the dialog body)
  // saves and exits edit mode.
  const handleRowBlur = (e: React.FocusEvent<HTMLDivElement>) => {
    const next = e.relatedTarget as Node | null;
    if (next && rowRef.current?.contains(next)) return;
    commit();
  };

  if (!editing) {
    return (
      <div
        ref={rowRef}
        data-new-row={isNew || undefined}
        className={cn(
          'group flex items-center gap-2 border-b px-3 py-2 text-sm transition-colors',
          'border-border/60 hover:bg-muted/40',
          isNew ? 'border-dashed opacity-60 hover:opacity-100' : ''
        )}
      >
        <span className="w-7 shrink-0 text-right font-mono text-xs text-muted-foreground">
          {index}
        </span>
        <span className="w-[110px] shrink-0 font-mono text-xs">{initialDate}</span>
        <span className="min-w-0 flex-1 truncate text-xs">{initialDetails}</span>
        <span
          className={cn(
            'w-[110px] shrink-0 text-right font-mono text-xs font-semibold',
            amount < 0 ? 'text-red-600 dark:text-red-400' : 'text-green-600 dark:text-green-400'
          )}
        >
          {amount < 0 ? '-' : '+'}
          {Math.abs(amount).toLocaleString('en-US', { maximumFractionDigits: 2 })}
        </span>
        <div className="flex shrink-0 items-center gap-1">
          {onDelete && !confirmDelete && (
            <button
              type="button"
              title="Edit row"
              onClick={() => {
                if (onEditingChange) onEditingChange(true);
              }}
              className="rounded p-1 text-muted-foreground opacity-0 transition-opacity hover:bg-muted hover:text-foreground group-hover:opacity-100"
            >
              <Pencil className="size-3.5" />
            </button>
          )}
          {onDelete && !confirmDelete && (
            <button
              type="button"
              title="Delete row"
              onClick={() => setConfirmDelete(true)}
              className="rounded p-1 text-muted-foreground opacity-0 transition-opacity hover:bg-destructive/10 hover:text-destructive group-hover:opacity-100"
            >
              <Trash2 className="size-3.5" />
            </button>
          )}
          {onDelete && confirmDelete && (
            <span className="flex items-center gap-1 rounded bg-destructive/10 px-1.5 py-0.5">
              <span className="text-[10px] text-destructive">Delete?</span>
              <button
                type="button"
                title="Confirm delete"
                onClick={() => {
                  setConfirmDelete(false);
                  onDelete();
                }}
                className="rounded p-0.5 text-destructive hover:bg-destructive/20"
              >
                <Check className="size-3" />
              </button>
              <button
                type="button"
                title="Cancel delete"
                onClick={() => setConfirmDelete(false)}
                className="rounded p-0.5 text-muted-foreground hover:bg-muted"
              >
                <X className="size-3" />
              </button>
            </span>
          )}
        </div>
      </div>
    );
  }

  // Editing mode — inputs pre-filled with the current values.
  return (
    <div
      ref={rowRef}
      onBlur={handleRowBlur}
      className="flex items-center gap-2 border-b border-border/60 bg-muted/30 px-3 py-1.5 text-sm"
    >
      <span className="w-7 shrink-0 text-right font-mono text-xs text-muted-foreground">
        {isNew ? '+' : index}
      </span>
      <input
        value={dateDraft}
        onChange={(e) => setDateDraft(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter') commit();
          if (e.key === 'Escape') cancel();
        }}
        placeholder="Date (e.g. 19-02-2023)"
        className="w-[110px] shrink-0 rounded border border-border bg-background px-1.5 py-1 font-mono text-xs outline-none focus:border-ring"
      />
      <input
        value={detailsDraft}
        onChange={(e) => setDetailsDraft(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter') commit();
          if (e.key === 'Escape') cancel();
        }}
        placeholder="Transaction details"
        className="min-w-0 flex-1 rounded border border-border bg-background px-1.5 py-1 text-xs outline-none focus:border-ring"
      />
      <input
        value={amountDraft}
        onChange={(e) => setAmountDraft(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter') commit();
          if (e.key === 'Escape') cancel();
        }}
        placeholder="Amount (no sign)"
        inputMode="decimal"
        className="w-[110px] shrink-0 rounded border border-border bg-background px-1.5 py-1 text-right font-mono text-xs outline-none focus:border-ring"
      />
      {error && <span className="shrink-0 text-[10px] text-destructive">{error}</span>}
      <div className="flex shrink-0 items-center gap-1">
        <button
          type="button"
          title="Save"
          onMouseDown={(e) => e.preventDefault()}
          onClick={commit}
          className="rounded p-1 text-green-600 hover:bg-green-500/10"
        >
          <Check className="size-3.5" />
        </button>
        <button
          type="button"
          title="Cancel"
          onMouseDown={(e) => e.preventDefault()}
          onClick={cancel}
          className="rounded p-1 text-muted-foreground hover:bg-muted"
        >
          <X className="size-3.5" />
        </button>
      </div>
    </div>
  );
}

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
