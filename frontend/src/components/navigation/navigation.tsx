/* بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */

/**
 * Navigation — the membership-aware application header.
 *
 * When the signed-in account holds a granted membership it shows the company it
 * belongs to and a confirmed "Leave company" action (FR-015), plus a "Company
 * Dashboard" shortcut only when the account is also a Manager (FR-020 — the
 * dashboard address stays hidden from everyone else). When there is no
 * membership, the application links are hidden and only the minimal header
 * remains, matching the gate (FR-009).
 */
'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useSession } from 'next-auth/react';
import { Building2, LayoutDashboard, Loader2, LogOut } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import SessionStatus from '@/components/auth/session-status';
import { ThemeToggle } from '@/components/theme/theme-toggle';
import { employeeClient } from '@/lib/api/employeeClient';
import type { Membership } from '@/types/employee.types';

const APP_LINK_CLASS =
  'text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-gray-100';

export function Navigation() {
  const { data: session } = useSession();
  const router = useRouter();
  const token = (session?.user as { access_token?: string } | undefined)?.access_token ?? '';

  const [membership, setMembership] = useState<Membership | null>(null);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [leaving, setLeaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    employeeClient
      .getMembership(token)
      .then((result) => {
        if (!cancelled) setMembership(result.membership);
      })
      .catch(() => {
        if (!cancelled) setMembership(null);
      });
    return () => {
      cancelled = true;
    };
  }, [token]);

  // Gate on the token too: when the session is gone, stale membership state is
  // ignored rather than cleared inside an effect.
  const isMember = Boolean(token) && Boolean(membership);
  // Application access additionally needs the company's free trial running.
  // The membership (and the Leave action) survive an inactive trial.
  const hasAccess = isMember && membership?.trial_active === true;

  const handleLeave = async () => {
    if (!token) return;
    setLeaving(true);
    setError(null);
    try {
      await employeeClient.removeMembership(token);
      setMembership(null);
      setConfirmOpen(false);
      router.push('/subscription');
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to leave the company.');
    } finally {
      setLeaving(false);
    }
  };

  return (
    <header className="flex items-center justify-between border-b border-gray-200 bg-white px-6 py-3 dark:border-gray-800 dark:bg-gray-950">
      <a
        href={hasAccess ? '/upload-ai' : '/subscription'}
        className="text-lg font-semibold text-gray-900 dark:text-gray-100"
      >
        Bank Reconciliation
      </a>

      <nav className="flex items-center gap-4 text-sm font-medium">
        {hasAccess && (
          <a href="/upload-ai" className={APP_LINK_CLASS}>
            Upload (AI)
          </a>
        )}

        {isMember && membership && (
          <span className="hidden items-center gap-1.5 text-gray-600 sm:inline-flex dark:text-gray-300">
            <Building2 className="size-4" />
            {membership.company_name}
          </span>
        )}

        {isMember && !hasAccess && (
          <span className="hidden items-center gap-1.5 rounded-full border border-amber-500/40 bg-amber-500/10 px-2 py-0.5 text-xs font-medium text-amber-700 sm:inline-flex dark:text-amber-400">
            Trial inactive
          </span>
        )}

        {isMember && membership?.is_manager && (
          <a href="/CompanyDashboard" className={`${APP_LINK_CLASS} inline-flex items-center gap-1.5`}>
            <LayoutDashboard className="size-4" />
            Company Dashboard
          </a>
        )}

        {isMember && (
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="gap-1"
            onClick={() => setConfirmOpen(true)}
          >
            <LogOut className="size-3" />
            Leave company
          </Button>
        )}

        <div className="flex items-center gap-3">
          <ThemeToggle />
          <SessionStatus />
        </div>
      </nav>

      <Dialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Leave company?</DialogTitle>
            <DialogDescription>
              This removes your access to the application and deletes your record from the
              company. You will need a new grant to use the app again.
            </DialogDescription>
          </DialogHeader>

          {error && <p className="text-sm text-destructive">{error}</p>}

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setConfirmOpen(false)}
              disabled={leaving}
            >
              Cancel
            </Button>
            <Button
              type="button"
              variant="destructive"
              className="gap-1"
              onClick={() => void handleLeave()}
              disabled={leaving}
            >
              {leaving ? <Loader2 className="size-4 animate-spin" /> : <LogOut className="size-4" />}
              Leave company
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </header>
  );
}

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
