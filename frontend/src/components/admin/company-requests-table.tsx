/* بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */

/**
 * CompanyRequestsTable — the Admin Dashboard's "Company Requests" category
 * (FR-006).
 *
 * Lists companies that asked to be onboarded, from the real
 * /api/admin/company-requests endpoint, and opens a detail dialog with the
 * submitted contact details so the Developer can reach out. The category is
 * view-only: a request never creates or links a company account.
 */
'use client';

import { useCallback, useEffect, useState } from 'react';
import {
  AlertCircle,
  Briefcase,
  ClipboardList,
  Globe,
  Mail,
  Phone,
  RefreshCw,
} from 'lucide-react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { adminClient } from '@/lib/api/adminClient';
import type { CompanyRequest } from '@/types/companyRequest.types';

type LoadState = 'loading' | 'ready' | 'error';

function DetailRow({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="flex items-start gap-2 text-sm">
      <span className="mt-0.5 text-muted-foreground">{icon}</span>
      <div>
        <p className="text-[11px] uppercase tracking-wide text-muted-foreground">{label}</p>
        <p className="font-medium">{value || '—'}</p>
      </div>
    </div>
  );
}

/** Render an ISO timestamp as a local, readable date-time (blank → em dash). */
function formatSubmitted(iso: string): string {
  const at = Date.parse(iso);
  if (Number.isNaN(at)) return '—';
  return new Date(at).toLocaleString();
}

interface CompanyRequestsTableProps {
  token: string;
}

export function CompanyRequestsTable({ token }: CompanyRequestsTableProps) {
  const [requests, setRequests] = useState<CompanyRequest[]>([]);
  const [state, setState] = useState<LoadState>('loading');
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<CompanyRequest | null>(null);

  // Plain fetch (no state) so the mount effect can populate state from promise
  // callbacks — no synchronous setState in the effect body.
  const fetchRequests = useCallback(() => adminClient.listCompanyRequests(token), [token]);

  const load = useCallback(async () => {
    if (!token) return;
    setState('loading');
    setError(null);
    try {
      const result = await fetchRequests();
      setRequests(result.requests);
      setState('ready');
    } catch (err) {
      setState('error');
      setError(err instanceof Error ? err.message : 'Failed to load company requests.');
    }
  }, [fetchRequests, token]);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    fetchRequests()
      .then((result) => {
        if (cancelled) return;
        setRequests(result.requests);
        setState('ready');
      })
      .catch((err) => {
        if (cancelled) return;
        setState('error');
        setError(err instanceof Error ? err.message : 'Failed to load company requests.');
      });
    return () => {
      cancelled = true;
    };
  }, [fetchRequests, token]);

  if (state === 'loading' && requests.length === 0) {
    return (
      <div className="space-y-2">
        {[0, 1, 2].map((row) => (
          <Skeleton key={row} className="h-14 w-full rounded-lg" />
        ))}
      </div>
    );
  }

  if (state === 'error') {
    return (
      <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-10 text-center">
        <AlertCircle className="mx-auto mb-2 size-6 text-destructive" />
        <p className="text-sm font-medium">Couldn&apos;t load company requests</p>
        <p className="mt-0.5 text-xs text-muted-foreground">{error}</p>
        <Button type="button" size="sm" variant="outline" className="mt-4 gap-1" onClick={() => void load()}>
          <RefreshCw className="size-3" />
          Try again
        </Button>
      </div>
    );
  }

  if (requests.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-border p-10 text-center">
        <ClipboardList className="mx-auto mb-2 size-6 text-muted-foreground" />
        <p className="text-sm font-medium">No company requests</p>
        <p className="mt-0.5 text-xs text-muted-foreground">
          Requests submitted through the onboarding flow will appear here.
        </p>
      </div>
    );
  }

  return (
    <>
      <div className="overflow-hidden rounded-lg border border-border">
        <Table>
          <TableHeader>
            <TableRow className="bg-muted/40">
              <TableHead>Company</TableHead>
              <TableHead>Role</TableHead>
              <TableHead>Website / Socials</TableHead>
              <TableHead>Email</TableHead>
              <TableHead>Phone</TableHead>
              <TableHead className="w-[190px]">Submitted</TableHead>
              <TableHead className="w-[90px] text-right">Details</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {requests.map((request) => (
              <TableRow key={request.id}>
                <TableCell className="font-medium">{request.company_name}</TableCell>
                <TableCell className="max-w-[220px] truncate text-sm text-muted-foreground">
                  {request.role || '—'}
                </TableCell>
                <TableCell className="text-sm">{request.website_socials || '—'}</TableCell>
                <TableCell className="text-sm">{request.email || '—'}</TableCell>
                <TableCell className="text-sm">{request.phone || '—'}</TableCell>
                <TableCell className="text-xs text-muted-foreground">
                  {formatSubmitted(request.submitted_at)}
                </TableCell>
                <TableCell>
                  <div className="flex justify-end">
                    <Button
                      type="button"
                      size="xs"
                      variant="outline"
                      onClick={() => setSelected(request)}
                    >
                      View
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <Dialog open={selected !== null} onOpenChange={(open) => !open && setSelected(null)}>
        <DialogContent className="sm:max-w-md">
          {selected && (
            <>
              <DialogHeader>
                <DialogTitle>{selected.company_name}</DialogTitle>
                <DialogDescription>
                  Submitted through the Company Request onboarding flow.
                </DialogDescription>
              </DialogHeader>

              <div className="space-y-4">
                <DetailRow
                  icon={<Briefcase className="size-4" />}
                  label="Role"
                  value={selected.role}
                />
                <DetailRow
                  icon={<Globe className="size-4" />}
                  label="Website / Socials"
                  value={selected.website_socials}
                />
                <DetailRow
                  icon={<Mail className="size-4" />}
                  label="Email"
                  value={selected.email}
                />
                <DetailRow
                  icon={<Phone className="size-4" />}
                  label="Phone"
                  value={selected.phone}
                />
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
