/* بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */

/**
 * EditPastFileDialog
 *
 * The past-file editor used for BOTH Edit and Create.
 *
 * - Edit: opens with the file's existing discrepancies grouped into the four
 *   category sections; the name can be renamed.
 * - Create: opens an empty file (name + Bank/Vendor toggle) with empty
 *   sections ready to be filled.
 *
 * Inside each section a full-width skeleton "+" row sits between the category
 * header and the first discrepancy; clicking it opens an empty Date/Details/
 * Amount row for that section (the section's sign is applied automatically).
 * Each row has an edit (pencil) action that makes the fields writable and
 * auto-saves on blur, plus a delete (trash) action with inline confirm.
 *
 * The footer carries a dark-green "Edit/Create with Excel" button. Clicking it
 * hides the table, auto-downloads the template (prefilled for Edit, empty for
 * Create), and shows an upload zone; uploading the filled file parses+saves on
 * the backend and returns to the table view with fresh data.
 */
'use client';

import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useSession } from 'next-auth/react';
import {
  Plus,
  FileSpreadsheet,
  Download,
  Loader2,
  AlertCircle,
  CheckCircle2,
  Save,
} from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';
import { cloudHistoryClient } from '@/lib/api/cloudHistoryClient';
import type {
  CloudHistoryEntry,
  PastFileReconciliationType,
} from '@/types/cloud-history.types';
import { EditableDiscrepancyRow } from './EditableDiscrepancyRow';
import { ExcelUploadZone } from './ExcelUploadZone';

// The four sections, in the canonical display order.
const BANK_SECTIONS = [
  'Unpresented Checks',
  'Uncleared Checks',
  'Bank Debited But not Credited in Cashbook',
  'Bank Credited But not Debited in Cashbook',
];

const VENDOR_SECTIONS = [
  'Unpresented Checks',
  'Uncleared Checks',
  'Vendor Debited but not Credited in Cashbook',
  'Vendor Credited But not Debited in Cashbook',
];

function sectionsForType(type: PastFileReconciliationType): string[] {
  return type === 'vendor' ? VENDOR_SECTIONS : BANK_SECTIONS;
}

interface EditPastFileDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** When provided, the dialog edits this file; otherwise it creates a new one. */
  fileId?: string;
  initialFileName?: string;
  initialType?: PastFileReconciliationType;
  /** Existing discrepancies (only passed for Edit — Create passes []). */
  initialEntries?: CloudHistoryEntry[];
  /** Called after a successful save so the drawer can refresh its list. */
  onSaved?: (fileId: string, fileName: string) => void;
}

interface RowEntry extends CloudHistoryEntry {
  /** Local key for React reconciliation. */
  _key: string;
}

function makeKey(): string {
  return `row-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

export function EditPastFileDialog({
  open,
  onOpenChange,
  fileId,
  initialFileName = '',
  initialType = 'bank',
  initialEntries = [],
  onSaved,
}: EditPastFileDialogProps) {
  const { data: session } = useSession();
  const token = (session?.user as { access_token?: string } | undefined)?.access_token;

  const isCreate = fileId == null;

  const [fileName, setFileName] = useState(initialFileName);
  const [reconciliationType, setReconciliationType] =
    useState<PastFileReconciliationType>(initialType);
  const [entriesBySection, setEntriesBySection] = useState<Record<string, RowEntry[]>>({});
  const [editingRowKey, setEditingRowKey] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Excel mode state.
  const [excelMode, setExcelMode] = useState(false);
  const [downloadingTemplate, setDownloadingTemplate] = useState(false);
  const [selectedExcelFile, setSelectedExcelFile] = useState<File | null>(null);
  const [importing, setImporting] = useState(false);

  // Track which open "session" this dialog was seeded for. Whenever the dialog
  // (re)opens with different props, reset the working copy — done during render
  // so the state is adjusted before the first paint (no cascading effect).
  const [seededFor, setSeededFor] = useState<string | null>(null);
  const [loadingFile, setLoadingFile] = useState(false);
  const seedKey = `${open ? 'open' : 'closed'}:${fileId ?? 'create'}:${initialFileName}:${initialType}:${initialEntries.length}`;
  if (seedKey !== seededFor) {
    setSeededFor(seedKey);
    if (open) {
      setFileName(initialFileName);
      setReconciliationType(initialType);
      setEditingRowKey(null);
      setError(null);
      setSuccess(null);
      setExcelMode(false);
      setSelectedExcelFile(null);
      setLoadingFile(false);

      const buckets: Record<string, RowEntry[]> = {};
      for (const section of sectionsForType(initialType)) buckets[section] = [];
      for (const entry of Array.isArray(initialEntries) ? initialEntries : []) {
        const section = buckets[entry.category]
          ? entry.category
          : sectionsForType(initialType).find((s) => s.toLowerCase() === (entry.category || '').toLowerCase());
        const target = section || sectionsForType(initialType)[0];
        buckets[target].push({ ...entry, _key: makeKey() });
      }
      setEntriesBySection(buckets);
    }
  }

  // Hard retrieve: when editing an existing file, always fetch the freshest
  // copy from the backend on open so edits made elsewhere (or via Excel)
  // are reflected — never trust a possibly-stale parent cache.
  const refreshedFor = useRef<string | null>(null);
  useEffect(() => {
    if (!open || fileId == null) return;
    const sessionKey = `${fileId}:${initialFileName}:${initialType}`;
    if (refreshedFor.current === sessionKey) return;
    refreshedFor.current = sessionKey;
    if (!token) return;
    let cancelled = false;
    setLoadingFile(true);
    cloudHistoryClient
      .loadPastFile(token, fileId)
      .then((resp) => {
        if (cancelled) return;
        setFileName(resp.file_name);
        setReconciliationType(resp.reconciliation_type);
        const buckets: Record<string, RowEntry[]> = {};
        for (const section of sectionsForType(resp.reconciliation_type)) buckets[section] = [];
        for (const entry of Array.isArray(resp.discrepancies) ? resp.discrepancies : []) {
          const section = buckets[entry.category]
            ? entry.category
            : sectionsForType(resp.reconciliation_type).find((s) =>
                s.toLowerCase() === (entry.category || '').toLowerCase()
              );
          const target = section || sectionsForType(resp.reconciliation_type)[0];
          buckets[target].push({ ...entry, _key: makeKey() });
        }
        setEntriesBySection(buckets);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load the file.');
        }
      })
      .finally(() => {
        if (!cancelled) setLoadingFile(false);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, fileId]);

  const sections = useMemo(
    () => sectionsForType(reconciliationType),
    [reconciliationType]
  );

  const sectionsWithEntries = useMemo(
    () => sections.map((section) => ({ section, entries: entriesBySection[section] ?? [] })),
    [sections, entriesBySection]
  );

  const totalCount = useMemo(
    () => Object.values(entriesBySection).reduce((sum, rows) => sum + rows.length, 0),
    [entriesBySection]
  );

  const updateEntry = useCallback(
    (section: string, key: string, updated: Omit<RowEntry, '_key'>) => {
      setEntriesBySection((prev) => ({
        ...prev,
        [section]: (prev[section] ?? []).map((row) =>
          row._key === key ? { ...row, ...updated } : row
        ),
      }));
    },
    []
  );

  const deleteEntry = useCallback((section: string, key: string) => {
    setEntriesBySection((prev) => ({
      ...prev,
      [section]: (prev[section] ?? []).filter((row) => row._key !== key),
    }));
  }, []);

  const addEntry = useCallback((section: string) => {
    const key = makeKey();
    setEntriesBySection((prev) => ({
      ...prev,
      [section]: [
        ...(prev[section] ?? []),
        {
          _key: key,
          category: section,
          transaction_date: '',
          transaction_details: '',
          debit_credit_amount: 0,
        },
      ],
    }));
    setEditingRowKey(key);
  }, []);

  const saveAll = async () => {
    if (!token) return;
    if (!fileName.trim()) {
      setError('Please give this file a name.');
      return;
    }
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      const fileData: CloudHistoryEntry[] = Object.values(entriesBySection)
        .flat()
        .filter((row) => row.transaction_date.trim() || row.transaction_details.trim())
        .map(({ _key, ...entry }) => {
          void _key;
          return entry;
        });

      if (isCreate) {
        const created = await cloudHistoryClient.createPastFile(token, {
          file_name: fileName.trim(),
          reconciliation_type: reconciliationType,
          file_data: fileData,
        });
        onSaved?.(created.file_id, created.file_name);
      } else {
        const updated = await cloudHistoryClient.updatePastFile(token, fileId, {
          file_name: fileName.trim(),
          file_data: fileData,
        });
        onSaved?.(updated.file_id, updated.file_name);
      }
      setSuccess('Saved successfully.');
      onOpenChange(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save the file.');
    } finally {
      setSaving(false);
    }
  };

  // ---- Excel flow ----------------------------------------------------------

  const handleExcelMode = async () => {
    if (!token) return;
    setError(null);
    setSuccess(null);
    setDownloadingTemplate(true);
    try {
      await cloudHistoryClient.downloadPastFileExcel(
        token,
        isCreate ? undefined : fileId,
        reconciliationType
      );
      setExcelMode(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to download the Excel template.');
    } finally {
      setDownloadingTemplate(false);
    }
  };

  const handleImportExcel = async () => {
    if (!token || !selectedExcelFile) return;
    setImporting(true);
    setError(null);
    setSuccess(null);
    try {
      const result = await cloudHistoryClient.importPastFileExcel(token, selectedExcelFile, {
        fileId: isCreate ? undefined : fileId,
        fileName: fileName.trim() || undefined,
        reconciliationType,
      });

      // Rebuild the table view from the parsed, saved data.
      const buckets: Record<string, RowEntry[]> = {};
      for (const section of sectionsForType(result.reconciliation_type ?? reconciliationType)) {
        buckets[section] = [];
      }
      for (const entry of result.discrepancies) {
        const target = buckets[entry.category]
          ? entry.category
          : sectionsForType(result.reconciliation_type ?? reconciliationType)[0];
        buckets[target].push({ ...entry, _key: makeKey() });
      }
      setEntriesBySection(buckets);
      setFileName(result.file_name);
      setExcelMode(false);
      setSelectedExcelFile(null);
      setSuccess(
        `Excel imported — ${result.entry_count} discrepancy${result.entry_count === 1 ? '' : 'ies'} saved.`
      );
      onSaved?.(result.file_id, result.file_name);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to import the Excel file.');
    } finally {
      setImporting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="flex max-h-[90dvh] flex-col gap-3 sm:max-w-3xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileSpreadsheet className="size-4 text-emerald-600 dark:text-emerald-400" />
            {isCreate ? 'Create Past Reconciliation' : 'Edit Past Reconciliation'}
          </DialogTitle>
          <DialogDescription>
            {isCreate
              ? 'Create a new empty past file — add discrepancies below or use the Excel template.'
              : 'Edit the discrepancies of this past file — changes save automatically per row.'}
          </DialogDescription>
        </DialogHeader>

        {error && (
          <div className="flex items-center gap-2 rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2 text-xs text-destructive">
            <AlertCircle className="size-4 shrink-0" /> {error}
          </div>
        )}
        {success && (
          <div className="flex items-center gap-2 rounded-md border border-emerald-500/30 bg-emerald-500/5 px-3 py-2 text-xs text-emerald-700 dark:text-emerald-400">
            <CheckCircle2 className="size-4 shrink-0" /> {success}
          </div>
        )}

        {!excelMode ? (
          <>
            {/* File name + type */}
            <div className="flex flex-wrap items-center gap-3">
              <div className="flex-1 min-w-[220px]">
                <label className="mb-1 block text-xs font-medium text-muted-foreground">
                  File name
                </label>
                <Input
                  value={fileName}
                  onChange={(e) => setFileName(e.target.value)}
                  placeholder="e.g. June Reconciliation"
                  className="h-8 text-sm"
                />
              </div>
              {isCreate && (
                <div>
                  <label className="mb-1 block text-xs font-medium text-muted-foreground">
                    Type
                  </label>
                  <div className="flex h-8 items-center overflow-hidden rounded-md border">
                    {(['bank', 'vendor'] as const).map((type) => (
                      <button
                        key={type}
                        type="button"
                        onClick={() => setReconciliationType(type)}
                        className={cn(
                          'px-3 py-1 text-xs font-medium capitalize transition-colors',
                          reconciliationType === type
                            ? 'bg-emerald-600 text-white'
                            : 'bg-transparent text-muted-foreground hover:bg-muted'
                        )}
                      >
                        {type}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Sections */}
            <div className="-mx-1 flex-1 space-y-3 overflow-y-auto px-1 pb-1">
              {loadingFile && (
                <div className="flex items-center justify-center gap-2 py-6 text-sm text-muted-foreground">
                  <Loader2 className="size-4 animate-spin" /> Loading file from database…
                </div>
              )}
              {sectionsWithEntries.map(({ section, entries }) => (
                <div key={section} className="overflow-hidden rounded-lg border">
                  <div className="flex items-center justify-between bg-emerald-900 px-3 py-2 dark:bg-emerald-950">
                    <span className="text-xs font-semibold uppercase tracking-wide text-emerald-50">
                      {section}
                    </span>
                    <span className="rounded-full bg-emerald-800/60 px-2 py-0.5 text-[10px] text-emerald-100">
                      {entries.length}
                    </span>
                  </div>

                  <div className="bg-background">
                    {/* Header row */}
                    <div className="flex items-center gap-2 border-b border-border/60 bg-muted/40 px-3 py-1.5 text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
                      <span className="w-7 shrink-0 text-right">#</span>
                      <span className="w-[110px] shrink-0">Date</span>
                      <span className="min-w-0 flex-1">Details</span>
                      <span className="w-[110px] shrink-0 text-right">Amount</span>
                      <span className="w-14 shrink-0" />
                    </div>

                    {/* Skeleton "+" row between category header and first row */}
                    <button
                      type="button"
                      onClick={() => addEntry(section)}
                      title={`Add discrepancy to ${section}`}
                      className="flex w-full items-center justify-center gap-1 border-b border-dashed border-border/60 py-2 text-xs text-muted-foreground transition-colors hover:bg-muted/50 hover:text-foreground"
                    >
                      <Plus className="size-3.5" />
                      <span>Add discrepancy</span>
                    </button>

                    {entries.length === 0 ? (
                      <p className="px-3 py-3 text-center text-xs text-muted-foreground">
                        No discrepancies in this category yet.
                      </p>
                    ) : (
                      entries.map((entry, i) => (
                        <EditableDiscrepancyRow
                          key={entry._key}
                          index={i + 1}
                          category={section}
                          date={entry.transaction_date}
                          details={entry.transaction_details}
                          amount={entry.debit_credit_amount}
                          editing={editingRowKey === entry._key}
                          onEditingChange={(editing) =>
                            setEditingRowKey(editing ? entry._key : null)
                          }
                          onSave={(values) => updateEntry(section, entry._key, {
                            category: section,
                            transaction_date: values.date,
                            transaction_details: values.details,
                            debit_credit_amount: values.amount,
                          })}
                          onDelete={() => deleteEntry(section, entry._key)}
                          onCancelEdit={() => setEditingRowKey(null)}
                        />
                      ))
                    )}
                  </div>
                </div>
              ))}

              {totalCount === 0 && (
                <p className="py-2 text-center text-xs text-muted-foreground">
                  This file is empty — use “Add discrepancy” in any category or the Excel
                  template below to fill it.
                </p>
              )}
            </div>
          </>
        ) : (
          /* ---- Excel mode: upload zone ---- */
          <div className="space-y-3">
            <div className="flex items-start gap-2 rounded-md border border-emerald-500/30 bg-emerald-500/5 px-3 py-2 text-xs text-emerald-800 dark:text-emerald-300">
              <Download className="mt-0.5 size-4 shrink-0" />
              <p>
                The Excel template has been downloaded. Fill in the Date, Details and
                Amount columns (no signs — they are applied automatically), then upload
                the file back here. Do not change the template structure.
              </p>
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-muted-foreground">
                File name {isCreate && <span className="text-destructive">*</span>}
              </label>
              <Input
                value={fileName}
                onChange={(e) => setFileName(e.target.value)}
                placeholder="e.g. June Reconciliation"
                className="h-8 text-sm"
              />
            </div>
            <ExcelUploadZone
              selectedFile={selectedExcelFile}
              onFileSelected={setSelectedExcelFile}
              onFileRemove={() => setSelectedExcelFile(null)}
            />
            <Button
              type="button"
              onClick={handleImportExcel}
              disabled={!selectedExcelFile || importing || !fileName.trim()}
              className="w-full bg-emerald-700 text-white hover:bg-emerald-800 dark:bg-emerald-600 dark:hover:bg-emerald-700"
            >
              {importing ? (
                <>
                  <Loader2 className="size-4 animate-spin" /> Importing…
                </>
              ) : (
                <>
                  <FileSpreadsheet className="size-4" /> Import Excel file
                </>
              )}
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => {
                setExcelMode(false);
                setSelectedExcelFile(null);
                setError(null);
              }}
              className="w-full"
            >
              Back to table view
            </Button>
          </div>
        )}

        <DialogFooter className="mt-2">
          {!excelMode && (
            <Button
              type="button"
              variant="outline"
              onClick={handleExcelMode}
              disabled={downloadingTemplate}
              className="mr-auto border-emerald-700 bg-emerald-700 text-white hover:bg-emerald-800 dark:border-emerald-600 dark:bg-emerald-600 dark:hover:bg-emerald-700"
            >
              {downloadingTemplate ? (
                <>
                  <Loader2 className="size-4 animate-spin" /> Downloading…
                </>
              ) : (
                <>
                  <FileSpreadsheet className="size-4" />
                  {isCreate ? 'Create with Excel' : 'Edit with Excel'}
                </>
              )}
            </Button>
          )}
          {!excelMode && (
            <Button type="button" onClick={saveAll} disabled={saving}>
              {saving ? (
                <>
                  <Loader2 className="size-4 animate-spin" /> Saving…
                </>
              ) : (
                <>
                  <Save className="size-4" /> Save file
                </>
              )}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
