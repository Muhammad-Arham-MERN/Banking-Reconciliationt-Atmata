/* بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */

/**
 * FilePreviewHoverCard
 *
 * The "View" affordance: hovering it opens a shadcn HoverCard containing a
 * Table with the whole file's discrepancies. Only 5 rows are visible; the
 * table body scrolls internally so all items can be reviewed.
 */
'use client';

import React, { useCallback, useState } from 'react';
import { useSession } from 'next-auth/react';
import { Eye, Loader2, AlertCircle } from 'lucide-react';
import {
  HoverCard,
  HoverCardTrigger,
  HoverCardContent,
} from '@/components/ui/hover-card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { cloudHistoryClient } from '@/lib/api/cloudHistoryClient';
import type { CloudHistoryEntry } from '@/types/cloud-history.types';
import { cn } from '@/lib/utils';

interface FilePreviewHoverCardProps {
  fileId: string;
  fileName: string;
  /** Signed wire amounts are shown as-is (bank credit + / debit -). */
  entries: CloudHistoryEntry[];
  /** Pre-fetched entries to avoid a fetch on first hover. */
  className?: string;
  /** Notified when the hover card fetches the full file (for parent caching). */
  onEntriesLoaded?: (entries: CloudHistoryEntry[]) => void;
}

export function FilePreviewHoverCard({
  fileId,
  fileName,
  entries,
  className,
  onEntriesLoaded,
}: FilePreviewHoverCardProps) {
  const { data: session } = useSession();
  const [loadedEntries, setLoadedEntries] = useState<CloudHistoryEntry[]>(entries);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // If the parent only has metadata, fetch the full file on first hover.
  const load = useCallback(() => {
    if (entries.length > 0) return;
    const token = (session?.user as { access_token?: string } | undefined)?.access_token;
    if (!token) return;
    setLoading(true);
    setError(null);
    cloudHistoryClient
      .loadPastFile(token, fileId)
      .then((resp) => {
        const loaded = Array.isArray(resp.discrepancies) ? resp.discrepancies : [];
        setLoadedEntries(loaded);
        onEntriesLoaded?.(loaded);
      })
      .catch((err) =>
        setError(err instanceof Error ? err.message : 'Failed to load file')
      )
      .finally(() => setLoading(false));
  }, [entries, fileId, session, onEntriesLoaded]);

  return (
    <HoverCard>
      <HoverCardTrigger
        render={<span />}
        className={cn('cursor-pointer', className)}
        onMouseEnter={load}
      >
        <span className="inline-flex items-center gap-1.5 rounded-md border border-blue-200 bg-blue-50 px-2.5 py-1 text-xs font-medium text-blue-700 transition-colors hover:bg-blue-100 dark:border-blue-900 dark:bg-blue-950/50 dark:text-blue-300 dark:hover:bg-blue-950">
          <Eye className="size-3.5" />
          View
        </span>
      </HoverCardTrigger>
      <HoverCardContent
        align="start"
        side="top"
        sideOffset={8}
        className="w-[520px] p-3"
      >
        <div className="mb-2 flex items-center justify-between gap-2">
          <p className="truncate text-sm font-semibold">{fileName}</p>
          <span className="shrink-0 rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">
            {loadedEntries.length} item{loadedEntries.length === 1 ? '' : 's'}
          </span>
        </div>

        {loading && (
          <div className="flex items-center justify-center gap-2 py-6 text-sm text-muted-foreground">
            <Loader2 className="size-4 animate-spin" /> Loading…
          </div>
        )}
        {error && (
          <div className="flex items-center gap-2 rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2 text-xs text-destructive">
            <AlertCircle className="size-4 shrink-0" /> {error}
          </div>
        )}
        {!loading && !error && loadedEntries.length === 0 && (
          <p className="py-6 text-center text-sm text-muted-foreground">
            This file has no discrepancies yet.
          </p>
        )}
        {!loading && !error && loadedEntries.length > 0 && (
          <div className="max-h-56 overflow-y-auto rounded-md border">
            <Table className="text-xs">
              <TableHeader className="sticky top-0 bg-muted/80 backdrop-blur">
                <TableRow>
                  <TableHead className="w-[110px]">Date</TableHead>
                  <TableHead>Details</TableHead>
                  <TableHead className="w-[110px] text-right">Amount</TableHead>
                  <TableHead className="w-[140px]">Category</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loadedEntries.map((entry, i) => (
                  <TableRow key={`${entry.transaction_date}-${i}`}>
                    <TableCell className="whitespace-nowrap font-mono">
                      {entry.transaction_date || '—'}
                    </TableCell>
                    <TableCell className="max-w-[220px] truncate">
                      {entry.transaction_details || '—'}
                    </TableCell>
                    <TableCell
                      className={cn(
                        'whitespace-nowrap text-right font-mono font-medium',
                        (entry.debit_credit_amount ?? 0) < 0
                          ? 'text-red-600 dark:text-red-400'
                          : 'text-green-600 dark:text-green-400'
                      )}
                    >
                      {(entry.debit_credit_amount ?? 0).toLocaleString('en-US', {
                        maximumFractionDigits: 2,
                      })}
                    </TableCell>
                    <TableCell className="whitespace-nowrap text-muted-foreground">
                      {entry.category}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </HoverCardContent>
    </HoverCard>
  );
}

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
