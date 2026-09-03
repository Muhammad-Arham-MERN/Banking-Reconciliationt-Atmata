/* بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */

/**
 * PastReconciliationsDrawer
 *
 * The "Past Reconciliations" drawer (right side, data-swipe-direction=right).
 * Lists every stored past file with Load / View / Edit / Delete actions and a
 * "+ Create" entry at the top. Loading the list happens on open + manual
 * Refresh (render-once, user-controlled — never on every session refetch).
 */
'use client';

import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useSession } from 'next-auth/react';
import {
  History,
  Plus,
  RefreshCw,
  Loader2,
  AlertCircle,
  Play,
  Check,
  Trash2,
  Ban,
} from 'lucide-react';
import {
  Drawer,
  DrawerClose,
  DrawerContent,
  DrawerDescription,
  DrawerFooter,
  DrawerHeader,
  DrawerTitle,
} from '@/components/ui/drawer';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { cloudHistoryClient } from '@/lib/api/cloudHistoryClient';
import type {
  PastFileMeta,
  CloudHistoryEntry,
  PastFileReconciliationType,
} from '@/types/cloud-history.types';
import { FilePreviewHoverCard } from './FilePreviewHoverCard';
import { EditPastFileDialog } from './EditPastFileDialog';

interface PastReconciliationsDrawerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** Called with the file name when the user clicks Load. */
  onLoadFile?: (fileName: string) => void;
}

export function PastReconciliationsDrawer({
  open,
  onOpenChange,
  onLoadFile,
}: PastReconciliationsDrawerProps) {
  const { data: session } = useSession();
  const token = (session?.user as { access_token?: string } | undefined)?.access_token;

  const [files, setFiles] = useState<PastFileMeta[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Create dialog state.
  const [createOpen, setCreateOpen] = useState(false);

  // Edit dialog state.
  const [editTarget, setEditTarget] = useState<PastFileMeta | null>(null);

  // Per-file cached entries (fetched lazily for the hover-card + edit dialog).
  const [entriesCache, setEntriesCache] = useState<Record<string, CloudHistoryEntry[]>>({});

  // Two-step delete confirmation.
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const loadedOnce = useRef(false);

  const loadFiles = useCallback(
    (force = false) => {
      if (!token) return;
      if (loadedOnce.current && !force) return;
      loadedOnce.current = true;
      setLoading(true);
      setError(null);
      // Hard retrieve: drop the per-file cache so hover/View and the Edit
      // dialog re-fetch fresh data from the database instead of stale copies.
      if (force) setEntriesCache({});
      cloudHistoryClient
        .listPastFiles(token)
        .then((resp) => setFiles(Array.isArray(resp.files) ? resp.files : []))
        .catch((err) =>
          setError(err instanceof Error ? err.message : 'Failed to load past reconciliations')
        )
        .finally(() => setLoading(false));
    },
    [token]
  );

  // Load once when the drawer first opens; manual Refresh afterwards.
  useEffect(() => {
    if (open) loadFiles(false);
  }, [open, loadFiles]);

  // Refresh when a create/edit save lands, so the list is fresh.
  const refreshAfterSave = useCallback(() => {
    loadFiles(true);
  }, [loadFiles]);

  const handleLoad = (file: PastFileMeta) => {
    onLoadFile?.(file.file_name);
    onOpenChange(false);
  };

  /** "None" — clear the selection so no past file merges in. */
  const handleLoadNone = () => {
    onLoadFile?.('');
    onOpenChange(false);
  };

  const handleDelete = async (file: PastFileMeta) => {
    if (!token) return;
    if (deleteConfirmId !== file.file_id) {
      setDeleteConfirmId(file.file_id);
      return;
    }
    setDeletingId(file.file_id);
    setError(null);
    try {
      await cloudHistoryClient.deletePastFile(token, file.file_id);
      setFiles((prev) => prev.filter((f) => f.file_id !== file.file_id));
      setDeleteConfirmId(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete the file.');
    } finally {
      setDeletingId(null);
    }
  };

  const openEditor = (file: PastFileMeta) => {
    setEditTarget(file);
  };

  const closeEditor = () => {
    setEditTarget(null);
    setCreateOpen(false);
  };

  const handleEditorSaved = useCallback(() => {
    refreshAfterSave();
    closeEditor();
  }, [refreshAfterSave]);

  return (
    <Drawer open={open} onOpenChange={onOpenChange} swipeDirection="right">
      <DrawerContent className="w-full sm:max-w-md">
        <DrawerHeader className="border-b">
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <History className="size-4 text-purple-600 dark:text-purple-400" />
              <DrawerTitle>Past Reconciliations</DrawerTitle>
            </div>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => loadFiles(true)}
              disabled={loading}
              title="Refresh list of past reconciliations"
            >
              <RefreshCw className={loading ? 'size-3.5 animate-spin' : 'size-3.5'} />
              Refresh
            </Button>
          </div>
          <DrawerDescription>
            View, edit, create or load a past reconciliation into a new one.
          </DrawerDescription>

          {/* Create entry at the top of the drawer */}
          <Button
            type="button"
            size="sm"
            onClick={() => {
              setEditTarget(null);
              setCreateOpen(true);
            }}
            className="mt-2 w-full bg-purple-600 text-white hover:bg-purple-700 dark:bg-purple-700 dark:hover:bg-purple-600"
          >
            <Plus className="size-4" />
            Create Past Reconciliation
          </Button>
        </DrawerHeader>

        <div className="flex-1 overflow-y-auto p-4">
          {error && (
            <div className="mb-3 flex items-center gap-2 rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2 text-xs text-destructive">
              <AlertCircle className="size-4 shrink-0" /> {error}
            </div>
          )}

          {/* "None" default — always available so a previous selection can be
              cleared even when the list is empty or still loading. */}
          <div className="mb-3 rounded-lg border border-dashed bg-card/50 p-3">
            <div className="flex items-center justify-between gap-2">
              <div className="min-w-0">
                <p className="text-sm font-semibold">None</p>
                <p className="mt-0.5 text-xs text-muted-foreground">
                  Go without any past reconciliation
                </p>
              </div>
              <Button
                type="button"
                size="xs"
                variant="outline"
                onClick={handleLoadNone}
                title="Clear the past-file selection"
                className="gap-1"
              >
                <Ban className="size-3" />
                Select
              </Button>
            </div>
          </div>

          {loading && files.length === 0 ? (
            <div className="space-y-3">
              {[0, 1, 2].map((i) => (
                <Skeleton key={i} className="h-20 w-full rounded-lg" />
              ))}
            </div>
          ) : files.length === 0 ? (
            <p className="py-8 text-center text-sm text-muted-foreground">
              No past reconciliations yet. Create one to get started.
            </p>
          ) : (
            <ul className="space-y-3">
              {files.map((file) => {
                const cachedEntries = entriesCache[file.file_id] ?? [];
                const isDeleting = deletingId === file.file_id;
                const showDeleteConfirm = deleteConfirmId === file.file_id;
                return (
                  <li
                    key={file.file_id}
                    className="rounded-lg border bg-card p-3 shadow-sm transition-shadow hover:shadow-md"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <div className="min-w-0">
                        <p className="truncate text-sm font-semibold">{file.file_name}</p>
                        <p className="mt-0.5 text-xs text-muted-foreground">
                          {file.entry_count} item{file.entry_count === 1 ? '' : 's'} ·{' '}
                          {new Date(file.created_at).toLocaleDateString()} ·{' '}
                          <span className="capitalize">{file.reconciliation_type}</span>
                        </p>
                      </div>
                    </div>

                    <div className="mt-2.5 flex flex-wrap items-center gap-1.5">
                      <Button
                        type="button"
                        size="xs"
                        variant="outline"
                        onClick={() => handleLoad(file)}
                        title="Load this file's discrepancies into the current reconciliation"
                        className="gap-1"
                      >
                        <Play className="size-3" />
                        Load
                      </Button>

                      <FilePreviewHoverCard
                        fileId={file.file_id}
                        fileName={file.file_name}
                        entries={cachedEntries}
                        onEntriesLoaded={(entries) =>
                          setEntriesCache((prev) => ({ ...prev, [file.file_id]: entries }))
                        }
                      />

                      <Button
                        type="button"
                        size="xs"
                        variant="outline"
                        onClick={() => openEditor(file)}
                        title="Edit this file's discrepancies"
                        className="gap-1"
                      >
                        Edit
                      </Button>

                      <Button
                        type="button"
                        size="xs"
                        variant="outline"
                        disabled={isDeleting}
                        onClick={() => handleDelete(file)}
                        title="Delete this file"
                        className={
                          showDeleteConfirm
                            ? 'gap-1 border-destructive bg-destructive/10 text-destructive hover:bg-destructive/20'
                            : 'gap-1 text-destructive hover:border-destructive/50 hover:bg-destructive/5'
                        }
                      >
                        {isDeleting ? (
                          <Loader2 className="size-3 animate-spin" />
                        ) : showDeleteConfirm ? (
                          <>
                            <Check className="size-3" /> Confirm?
                          </>
                        ) : (
                          <Trash2 className="size-3" />
                        )}
                        {!isDeleting && !showDeleteConfirm && 'Delete'}
                      </Button>
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </div>

        <DrawerFooter className="border-t">
          <DrawerClose render={<Button variant="outline" />}>Close</DrawerClose>
        </DrawerFooter>
      </DrawerContent>

      {/* Create dialog */}
      <EditPastFileDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        initialFileName=""
        initialType="bank"
        initialEntries={[]}
        onSaved={handleEditorSaved}
      />

      {/* Edit dialog */}
      <EditPastFileDialog
        open={editTarget != null}
        onOpenChange={(next) => {
          if (!next) setEditTarget(null);
        }}
        fileId={editTarget?.file_id}
        initialFileName={editTarget?.file_name ?? ''}
        initialType={(editTarget?.reconciliation_type as PastFileReconciliationType) ?? 'bank'}
        initialEntries={editTarget ? entriesCache[editTarget.file_id] ?? [] : []}
        onSaved={handleEditorSaved}
      />
    </Drawer>
  );
}

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
