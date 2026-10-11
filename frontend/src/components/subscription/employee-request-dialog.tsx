/* بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */

/**
 * EmployeeRequestDialog
 *
 * Ask a company to grant access. The employee supplies their name, an ID they
 * type or generate, and the company to request. The ID always ends up
 * `adam-` prefixed and unique per company — the server is the authority; this
 * form only normalizes and pre-checks what it can, so a tampered or hand-typed
 * value cannot bypass the rules.
 */
'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useSession } from 'next-auth/react';
import {
  AlertCircle,
  Building2,
  CheckCircle2,
  Dices,
  Loader2,
  RefreshCw,
  XCircle,
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { EmployeeApiError, employeeClient } from '@/lib/api/employeeClient';
import type { CompanyOption, EmployeeRequestResponse } from '@/types/employee.types';

/** Shown verbatim after a successful submit (FR-012). */
const CONFIRMATION_MESSAGE =
  'Your request has been sent to the designated company successfully, you may contact them to grant you access by providing them your ID or Name';

/**
 * Object URLs are cached for the page's lifetime: the select unmounts and
 * remounts its items on every open, so refetching each logo every time would
 * be wasteful. A handful of tiny images makes that a fair trade.
 */
const logoCache = new Map<string, string>();

/**
 * The backend refuses a second active request with 409 active_request_exists
 * (FR-017). Detect it from the typed error's raw payload so the dialog can
 * offer the cancel path instead of a generic failure.
 */
function isActiveRequestError(err: unknown): boolean {
  if (!(err instanceof EmployeeApiError) || err.status !== 409) return false;
  const details = err.details as { detail?: { error?: string } } | undefined;
  return details?.detail?.error === 'active_request_exists';
}

// وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
/** A random ID in the shape the server accepts: `adam-` + 8 chars of [a-z0-9]. */
function generateEmployeeId(): string {
  const alphabet = 'abcdefghijklmnopqrstuvwxyz0123456789';
  const bytes = new Uint32Array(8);
  crypto.getRandomValues(bytes);
  return `adam-${Array.from(bytes, (b) => alphabet[b % alphabet.length]).join('')}`;
}

/** A company's logo, or a placeholder when it has none / it cannot be loaded. */
function CompanyLogo({ token, company }: { token: string; company: CompanyOption }) {
  const [url, setUrl] = useState<string | null>(() => logoCache.get(company.id) ?? null);

  useEffect(() => {
    if (!company.logo_url || url) return;
    let cancelled = false;
    employeeClient.fetchLogoBlob(token, company.id).then((objectUrl) => {
      if (!objectUrl) return;
      logoCache.set(company.id, objectUrl);
      if (!cancelled) setUrl(objectUrl);
    });
    return () => {
      cancelled = true;
    };
  }, [company.id, company.logo_url, token, url]);

  if (!company.logo_url || !url) {
    return <Building2 className="size-4 shrink-0 text-muted-foreground" />;
  }
  return <img src={url} alt="" className="size-4 shrink-0 rounded object-cover" />;
}

/** The company dropdown is always in exactly one of these states. */
type ListState =
  | { status: 'loading' }
  | { status: 'ready'; companies: CompanyOption[] }
  | { status: 'error'; message: string };

interface EmployeeRequestDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function EmployeeRequestDialog({
  open,
  onOpenChange,
}: EmployeeRequestDialogProps) {
  const { data: session } = useSession();
  const router = useRouter();
  const token =
    (session?.user as { access_token?: string } | undefined)?.access_token ?? '';

  const [name, setName] = useState('');
  const [employeeId, setEmployeeId] = useState('');
  const [companyId, setCompanyId] = useState('');

  const [list, setList] = useState<ListState>({ status: 'loading' });
  const [reloadKey, setReloadKey] = useState(0);

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<EmployeeRequestResponse | null>(null);
  // Set when the submit is refused because the account already has an active
  // request; drives the "Cancel request" affordance (FR-017).
  const [activeRequest, setActiveRequest] = useState(false);
  const [cancelling, setCancelling] = useState(false);

  // Start from a clean form every time the dialog opens. Done during render,
  // before paint, so it cannot cascade an extra render (same pattern as
  // CompanyFormDialog).
  const [seededFor, setSeededFor] = useState<string | null>(null);
  const seedKey = open ? 'open' : 'closed';
  if (seedKey !== seededFor) {
    setSeededFor(seedKey);
    if (open) {
      setName('');
      setEmployeeId('');
      setCompanyId('');
      setError(null);
      setSuccess(null);
      setSubmitting(false);
      setActiveRequest(false);
      setCancelling(false);
      setReloadKey(0);
      setList({ status: 'loading' });
    }
  }

  // State is written only from the promise callbacks and from event handlers,
  // never synchronously inside the effect body, so the fetch cannot cascade an
  // extra render.
  useEffect(() => {
    if (!open || !token) return;
    let cancelled = false;
    employeeClient
      .listCompanies(token)
      .then((result) => {
        if (!cancelled) setList({ status: 'ready', companies: result.companies });
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        // A fetch failure is NOT the same as "no companies yet" — the two are
        // shown differently so a signed-in employee can tell an outage from an
        // empty roster (FR-009).
        setList({
          status: 'error',
          message:
            err instanceof EmployeeApiError && err.status === 401
              ? 'Your session has expired. Please sign in again.'
              : "Couldn't load companies. Please try again.",
        });
      });
    return () => {
      cancelled = true;
    };
  }, [open, token, reloadKey]);

  const companies = list.status === 'ready' ? list.companies : [];
  const listUnavailable = list.status !== 'ready';

  // Base UI renders the raw value in the trigger unless it knows the labels,
  // which for us would show the numeric company id instead of the name.
  const companyItems = companies.map((company) => ({
    value: company.id,
    label: company.name,
  }));

  const handleRetry = () => {
    setList({ status: 'loading' });
    setReloadKey((key) => key + 1);
  };

  const handleSubmit = async () => {
    if (!name.trim()) {
      setError('Enter the employee name.');
      return;
    }
    if (!employeeId.trim()) {
      setError('Enter or generate an employee ID.');
      return;
    }
    if (!companyId) {
      setError('Choose a company to request.');
      return;
    }

    setSubmitting(true);
    setError(null);
    setActiveRequest(false);
    try {
      const record = await employeeClient.createRequest(token, {
        employee_name: name.trim(),
        employee_id: employeeId.trim(),
        company_id: companyId,
      });
      setSuccess(record);
      // A pending request is not a membership yet, but refresh so every
      // membership-aware surface re-reads the current state.
      router.refresh();
    } catch (err) {
      if (isActiveRequestError(err)) {
        setActiveRequest(true);
      } else {
        setError(err instanceof Error ? err.message : 'Failed to send the request.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handleCancelRequest = async () => {
    if (!token) return;
    setCancelling(true);
    setError(null);
    try {
      // DELETE /api/me/membership removes the account's employee row — the
      // pending request — from the company's records (FR-017).
      await employeeClient.removeMembership(token);
      setActiveRequest(false);
      router.refresh();
      onOpenChange(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to cancel the request.');
    } finally {
      setCancelling(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        {success ? (
          <>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <CheckCircle2 className="size-4 text-emerald-600 dark:text-emerald-400" />
                Request sent
              </DialogTitle>
            </DialogHeader>

            <p className="text-sm">{CONFIRMATION_MESSAGE}</p>

            <div className="rounded-md border bg-muted/50 px-3 py-2 text-xs">
              <span className="text-muted-foreground">Your ID: </span>
              <span className="font-mono font-medium">{success.employee_id}</span>
            </div>

            <DialogFooter>
              <Button type="button" onClick={() => onOpenChange(false)}>
                Close
              </Button>
            </DialogFooter>
          </>
        ) : (
          <>
            <DialogHeader>
              <DialogTitle>Employee Request</DialogTitle>
              <DialogDescription>
                Ask a company to grant you access. They will use your ID or name.
              </DialogDescription>
            </DialogHeader>

            {error && (
              <div className="flex items-start gap-2 rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2 text-xs text-destructive">
                <AlertCircle className="mt-0.5 size-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {activeRequest && (
              <div className="space-y-2 rounded-md border border-amber-500/40 bg-amber-500/5 px-3 py-2 text-xs">
                <div className="flex items-start gap-2">
                  <XCircle className="mt-0.5 size-4 shrink-0 text-amber-600 dark:text-amber-400" />
                  <div>
                    <p className="font-medium text-amber-700 dark:text-amber-400">
                      You already have an active request
                    </p>
                    <p className="mt-0.5 text-muted-foreground">
                      Cancel it before requesting access to any company again.
                    </p>
                  </div>
                </div>
                <div className="flex justify-end">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    className="gap-1"
                    onClick={() => void handleCancelRequest()}
                    disabled={cancelling}
                  >
                    {cancelling ? (
                      <Loader2 className="size-3.5 animate-spin" />
                    ) : (
                      <XCircle className="size-3.5" />
                    )}
                    Cancel request
                  </Button>
                </div>
              </div>
            )}

            <div className="space-y-4">
              {/* Employee name */}
              <div>
                <label className="mb-1 block text-xs font-medium text-muted-foreground">
                  Employee Name <span className="text-destructive">*</span>
                </label>
                <Input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Bilal Ahmed"
                  className="h-9 text-sm"
                  disabled={submitting}
                />
              </div>

              {/* Employee ID */}
              <div>
                <label className="mb-1 block text-xs font-medium text-muted-foreground">
                  ID <span className="text-destructive">*</span>
                </label>
                <div className="flex items-center gap-2">
                  <Input
                    value={employeeId}
                    onChange={(e) => setEmployeeId(e.target.value)}
                    placeholder="Generate or type an ID"
                    className="h-9 flex-1 text-sm"
                    disabled={submitting}
                  />
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setEmployeeId(generateEmployeeId());
                      setError(null);
                    }}
                    disabled={submitting}
                    title="Generate a random ID"
                  >
                    <Dices className="size-3.5" /> Generate
                  </Button>
                </div>
                <p className="mt-1 text-[11px] text-muted-foreground">
                  6–12 letters or digits. The <span className="font-mono">adam-</span>{' '}
                  prefix is added for you.
                </p>
              </div>

              {/* Company to request */}
              <div>
                <label className="mb-1 block text-xs font-medium text-muted-foreground">
                  Company to Request <span className="text-destructive">*</span>
                </label>

                {list.status === 'error' ? (
                  <div className="flex items-center gap-2 rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2 text-xs text-destructive">
                    <AlertCircle className="size-4 shrink-0" />
                    <span className="flex-1">{list.message}</span>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={handleRetry}
                    >
                      <RefreshCw className="size-3.5" /> Retry
                    </Button>
                  </div>
                ) : list.status === 'loading' ? (
                  <div className="flex h-9 items-center gap-2 rounded-md border px-3 text-xs text-muted-foreground">
                    <Loader2 className="size-3.5 animate-spin" /> Loading companies…
                  </div>
                ) : list.companies.length === 0 ? (
                  <div className="rounded-md border border-dashed px-3 py-2 text-xs text-muted-foreground">
                    No companies are available yet.
                  </div>
                ) : (
                  <Select
                    items={companyItems}
                    value={companyId || null}
                    onValueChange={(value) => setCompanyId(value ?? '')}
                    disabled={submitting}
                  >
                    <SelectTrigger className="h-9 w-full">
                      <SelectValue placeholder="Choose a company" />
                    </SelectTrigger>
                    <SelectContent>
                      {companies.map((company) => (
                        <SelectItem key={company.id} value={company.id}>
                          <span className="flex items-center gap-2">
                            <CompanyLogo token={token} company={company} />
                            {company.name}
                          </span>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              </div>
            </div>

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
                disabled={submitting}
              >
                Cancel
              </Button>
              <Button
                type="button"
                onClick={handleSubmit}
                disabled={submitting || listUnavailable || companies.length === 0}
              >
                {submitting ? (
                  <>
                    <Loader2 className="size-4 animate-spin" /> Sending…
                  </>
                ) : (
                  'Send Request'
                )}
              </Button>
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
