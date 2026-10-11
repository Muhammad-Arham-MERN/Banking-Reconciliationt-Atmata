/* بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */

/**
 * CompaniesTable
 *
 * The single-page list of onboarded companies. Shows the logo, name, a masked
 * password with reveal/copy, the price in Rupees, the payment status, and
 * per-row Edit / Delete actions.
 *
 * Logos are served by an authenticated endpoint, so they are fetched as blobs
 * with the admin token (a bare <img src> would be rejected with 401).
 */
'use client';

import React, { useCallback, useEffect, useState } from 'react';
import {
  AlertCircle,
  Building2,
  Check,
  Copy,
  Eye,
  EyeOff,
  Loader2,
  Pencil,
  Trash2,
  Users,
} from 'lucide-react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from '@/components/ui/hover-card';
import { cn } from '@/lib/utils';
import { adminClient } from '@/lib/api/adminClient';
import { EMPLOYEE_STATUS_LABELS } from '@/types/employee.types';
import {
  PAYMENT_STATUS_LABELS,
  type AdminEmployee,
  type Company,
  type PaymentStatus,
} from '@/types/admin.types';

function statusBadgeClass(status: PaymentStatus): string {
  switch (status) {
    case 'paid':
      return 'bg-emerald-600 text-white';
    case 'free_trial':
      return 'border-amber-500/40 bg-amber-500/10 text-amber-700 dark:text-amber-400';
    default:
      return 'border-border bg-muted text-muted-foreground';
  }
}

/** Fetches a logo with the admin token and renders it from a blob URL. */
function CompanyLogo({ token, company }: { token: string; company: Company }) {
  const [url, setUrl] = useState<string | null>(null);

  useEffect(() => {
    if (!company.logo_url) return;
    let cancelled = false;
    let objectUrl: string | null = null;

    adminClient
      .fetchLogoBlob(token, company.id)
      .then((result) => {
        if (cancelled) {
          if (result) URL.revokeObjectURL(result);
          return;
        }
        objectUrl = result;
        setUrl(result);
      })
      .catch(() => setUrl(null));

    return () => {
      cancelled = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [token, company.id, company.logo_url, company.updated_at]);

  if (!company.logo_url) {
    return (
      <div className="flex size-9 items-center justify-center rounded-md border border-dashed border-border bg-muted/40">
        <Building2 className="size-4 text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="flex size-9 items-center justify-center overflow-hidden rounded-md border border-border bg-white dark:bg-gray-900">
      {url ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={url} alt={`${company.name} logo`} className="size-full object-contain" />
      ) : (
        <Skeleton className="size-full rounded-none" />
      )}
    </div>
  );
}

/**
 * Employee count with a hover modal listing the company's roster (FR-018). The
 * roster is fetched lazily on first hover, with loading/empty/error states.
 */
function EmployeeCount({ token, company }: { token: string; company: Company }) {
  const [open, setOpen] = useState(false);
  const [state, setState] = useState<'idle' | 'loading' | 'ready' | 'error'>('idle');
  const [employees, setEmployees] = useState<AdminEmployee[]>([]);
  const [error, setError] = useState<string | null>(null);

  const handleOpenChange = (next: boolean) => {
    setOpen(next);
    if (!next || state !== 'idle') return;
    setState('loading');
    adminClient
      .listCompanyEmployees(token, company.id)
      .then((result) => {
        setEmployees(result.employees);
        setState('ready');
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : 'Could not load employees.');
        setState('error');
      });
  };

  return (
    <HoverCard open={open} onOpenChange={handleOpenChange}>
      <HoverCardTrigger
        render={
          <button
            type="button"
            className="inline-flex items-center gap-1 rounded-md border border-border px-2 py-0.5 text-xs font-medium hover:bg-muted"
          >
            <Users className="size-3" />
            {company.employee_count}
          </button>
        }
      />
      <HoverCardContent align="start" className="w-72">
        <p className="mb-2 text-xs font-semibold">Employees ({company.employee_count})</p>

        {state === 'loading' && (
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Loader2 className="size-3 animate-spin" /> Loading…
          </div>
        )}

        {state === 'error' && <p className="text-xs text-destructive">{error}</p>}

        {state === 'ready' && employees.length === 0 && (
          <p className="text-xs text-muted-foreground">No employees yet.</p>
        )}

        {state === 'ready' && employees.length > 0 && (
          <ul className="max-h-64 space-y-2 overflow-y-auto">
            {employees.map((employee) => (
              <li key={employee.id} className="flex items-center justify-between gap-2 text-xs">
                <span className="min-w-0">
                  <span className="block truncate font-medium">{employee.employee_name}</span>
                  <span className="font-mono text-[11px] text-muted-foreground">
                    {employee.employee_id}
                  </span>
                </span>
                <Badge variant="outline" className="shrink-0">
                  {EMPLOYEE_STATUS_LABELS[employee.status]}
                </Badge>
              </li>
            ))}
          </ul>
        )}
      </HoverCardContent>
    </HoverCard>
  );
}

interface CompaniesTableProps {
  companies: Company[];
  loading: boolean;
  token: string;
  onEdit: (company: Company) => void;
  onDelete: (company: Company) => Promise<void>;
  onReveal: (company: Company) => Promise<string>;
}

export function CompaniesTable({
  companies,
  loading,
  token,
  onEdit,
  onDelete,
  onReveal,
}: CompaniesTableProps) {
  // Revealed passwords, keyed by company id (masked until revealed).
  const [revealed, setRevealed] = useState<Record<string, string>>({});
  const [revealing, setRevealing] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [rowError, setRowError] = useState<string | null>(null);

  // Two-step delete confirmation, mirroring PastReconciliationsDrawer.
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const handleReveal = useCallback(
    async (company: Company) => {
      setRowError(null);
      if (revealed[company.id]) {
        setRevealed((prev) => {
          const next = { ...prev };
          delete next[company.id];
          return next;
        });
        return;
      }
      setRevealing(company.id);
      try {
        const password = await onReveal(company);
        setRevealed((prev) => ({ ...prev, [company.id]: password }));
      } catch (err) {
        setRowError(
          err instanceof Error ? err.message : 'Could not reveal the password.'
        );
      } finally {
        setRevealing(null);
      }
    },
    [onReveal, revealed]
  );

  const handleCopy = useCallback(async (company: Company) => {
    try {
      const password = revealed[company.id] ?? (await onReveal(company));
      await navigator.clipboard.writeText(password);
      setRevealed((prev) => ({ ...prev, [company.id]: password }));
      setCopiedId(company.id);
      window.setTimeout(() => setCopiedId(null), 1500);
    } catch (err) {
      setRowError(err instanceof Error ? err.message : 'Could not copy the password.');
    }
  }, [onReveal, revealed]);

  const handleDelete = async (company: Company) => {
    setRowError(null);
    if (deleteConfirmId !== company.id) {
      setDeleteConfirmId(company.id);
      return;
    }
    setDeletingId(company.id);
    try {
      await onDelete(company);
      setDeleteConfirmId(null);
    } catch (err) {
      setRowError(err instanceof Error ? err.message : 'Could not delete the company.');
    } finally {
      setDeletingId(null);
    }
  };

  if (loading && companies.length === 0) {
    return (
      <div className="space-y-2">
        {[0, 1, 2].map((i) => (
          <Skeleton key={i} className="h-14 w-full rounded-lg" />
        ))}
      </div>
    );
  }

  if (!loading && companies.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-border p-10 text-center">
        <Building2 className="mx-auto mb-2 size-6 text-muted-foreground" />
        <p className="text-sm font-medium">No companies yet</p>
        <p className="mt-0.5 text-xs text-muted-foreground">
          Use “+ Add Companies” to register your first client.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {rowError && (
        <div className="flex items-center gap-2 rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2 text-xs text-destructive">
          <AlertCircle className="size-4 shrink-0" /> {rowError}
        </div>
      )}

      <div className="overflow-hidden rounded-lg border border-border">
        <Table>
          <TableHeader>
            <TableRow className="bg-muted/40">
              <TableHead className="w-[60px]">Logo</TableHead>
              <TableHead>Company</TableHead>
              <TableHead>Password</TableHead>
              <TableHead className="text-right">Price (Rs)</TableHead>
              <TableHead>Payment Status</TableHead>
              <TableHead className="w-[110px]">Employees</TableHead>
              <TableHead className="w-[160px] text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {companies.map((company) => {
              const isRevealed = Boolean(revealed[company.id]);
              const isDeleting = deletingId === company.id;
              const showDeleteConfirm = deleteConfirmId === company.id;

              return (
                <TableRow key={company.id}>
                  <TableCell>
                    <CompanyLogo token={token} company={company} />
                  </TableCell>

                  <TableCell className="max-w-[220px] truncate font-medium">
                    {company.name}
                  </TableCell>

                  <TableCell>
                    <div className="flex items-center gap-1.5">
                      <span className="font-mono text-xs">
                        {isRevealed ? revealed[company.id] : '••••••••'}
                      </span>
                      <Button
                        type="button"
                        size="icon-xs"
                        variant="ghost"
                        onClick={() => handleReveal(company)}
                        disabled={revealing === company.id}
                        title={isRevealed ? 'Hide password' : 'Reveal password'}
                      >
                        {revealing === company.id ? (
                          <Loader2 className="size-3 animate-spin" />
                        ) : isRevealed ? (
                          <EyeOff />
                        ) : (
                          <Eye />
                        )}
                      </Button>
                      <Button
                        type="button"
                        size="icon-xs"
                        variant="ghost"
                        onClick={() => handleCopy(company)}
                        title="Copy password"
                      >
                        {copiedId === company.id ? <Check /> : <Copy />}
                      </Button>
                    </div>
                  </TableCell>

                  <TableCell className="text-right font-mono text-xs">
                    {company.price_rupees.toLocaleString()}
                  </TableCell>

                  <TableCell>
                    <Badge
                      variant="outline"
                      className={cn('border', statusBadgeClass(company.payment_status))}
                    >
                      {PAYMENT_STATUS_LABELS[company.payment_status]}
                    </Badge>
                  </TableCell>

                  <TableCell>
                    <EmployeeCount token={token} company={company} />
                  </TableCell>

                  <TableCell>
                    <div className="flex items-center justify-end gap-1.5">
                      <Button
                        type="button"
                        size="xs"
                        variant="outline"
                        onClick={() => onEdit(company)}
                        title="Edit this company"
                        className="gap-1"
                      >
                        <Pencil className="size-3" />
                        Edit
                      </Button>

                      <Button
                        type="button"
                        size="xs"
                        variant="outline"
                        disabled={isDeleting}
                        onClick={() => handleDelete(company)}
                        title="Delete this company"
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
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
