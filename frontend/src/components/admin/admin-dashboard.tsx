/* بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */

/**
 * AdminDashboard (Camri Desk)
 *
 * The whole hidden AdminDashAccess surface. Holds the admin token for the
 * BROWSER SESSION ONLY (sessionStorage — closing the browser signs you out),
 * renders the sign-in form when there is no token, and otherwise shows a
 * category sidebar: Companies (the onboarded clients) and Company Requests
 * (companies that asked to be onboarded).
 *
 * Any 401 from the API means the admin session is over: the token is dropped
 * and the sign-in form comes back.
 */
'use client';

import React, { useCallback, useEffect, useState, useSyncExternalStore } from 'react';
import {
  AlertCircle,
  Building2,
  ClipboardList,
  LogOut,
  Plus,
  RefreshCw,
  ShieldCheck,
} from 'lucide-react';
import { motion, useReducedMotion } from 'motion/react';
import { Button } from '@/components/ui/button';
import {
  Sidebar,
  SidebarBody,
  SidebarLink,
  useSidebar,
} from '@/components/ui/sidebar';
import { cn } from '@/lib/utils';
import { adminClient, AdminApiError } from '@/lib/api/adminClient';
import {
  getAdminSessionServerSnapshot,
  getAdminSessionSnapshot,
  setAdminToken,
  subscribeToAdminSession,
} from '@/lib/admin/admin-session';
import { AdminSignInForm } from '@/components/admin/admin-sign-in-form';
import { CompaniesTable } from '@/components/admin/companies-table';
import { CompanyFormDialog } from '@/components/admin/company-form-dialog';
import { CompanyRequestsTable } from '@/components/admin/company-requests-table';
import type { Company } from '@/types/admin.types';

type AdminCategory = 'companies' | 'requests';

function isUnauthorized(err: unknown): boolean {
  return err instanceof AdminApiError && err.status === 401;
}

function describeError(err: unknown, fallback: string): string {
  return err instanceof Error ? err.message : fallback;
}

/** Plain data fetch (no state) so callers control their own loading UI. */
async function fetchCompanyList(token: string): Promise<Company[]> {
  const response = await adminClient.listCompanies(token);
  return response.companies;
}

/** A sidebar label that collapses with the sidebar, like the link labels. */
function SidebarHeading({ children }: { children: React.ReactNode }) {
  const { open, animate } = useSidebar();
  const reduceMotion = useReducedMotion();
  return (
    <motion.span
      animate={{
        display: animate ? (open ? 'inline-block' : 'none') : 'inline-block',
        opacity: animate ? (open ? 1 : 0) : 1,
      }}
      transition={reduceMotion ? { duration: 0 } : undefined}
      className="truncate text-sm font-semibold"
    >
      {children}
    </motion.span>
  );
}

export function AdminDashboard() {
  // Reads sessionStorage via an external store: no effect, no hydration
  // mismatch (the server snapshot is always "signed out").
  const token = useSyncExternalStore(
    subscribeToAdminSession,
    getAdminSessionSnapshot,
    getAdminSessionServerSnapshot,
  );

  const [category, setCategory] = useState<AdminCategory>('companies');
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editTarget, setEditTarget] = useState<Company | null>(null);

  const signOut = useCallback(() => {
    setAdminToken(null);
    setCompanies([]);
    setError(null);
    setDialogOpen(false);
    setEditTarget(null);
    setCategory('companies');
  }, []);

  // Load the list whenever a token is present (first paint after restoring the
  // session, and immediately after signing in). All state updates happen in
  // promise callbacks, never synchronously in the effect body.
  useEffect(() => {
    if (!token) return;
    let cancelled = false;

    fetchCompanyList(token)
      .then((list) => {
        if (cancelled) return;
        setCompanies(list);
        setError(null);
      })
      .catch((err) => {
        if (cancelled) return;
        if (isUnauthorized(err)) {
          signOut();
          return;
        }
        setError(describeError(err, 'Failed to load companies.'));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [token, signOut]);

  const handleSignedIn = useCallback((newToken: string) => {
    setLoading(true);
    setAdminToken(newToken);
  }, []);

  const refresh = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    try {
      setCompanies(await fetchCompanyList(token));
      setError(null);
    } catch (err) {
      if (isUnauthorized(err)) {
        signOut();
        return;
      }
      setError(describeError(err, 'Failed to load companies.'));
    } finally {
      setLoading(false);
    }
  }, [token, signOut]);

  const handleSaved = useCallback(async () => {
    setEditTarget(null);
    await refresh();
  }, [refresh]);

  const handleDelete = useCallback(
    async (company: Company) => {
      if (!token) return;
      try {
        await adminClient.deleteCompany(token, company.id);
        setCompanies((prev) => prev.filter((c) => c.id !== company.id));
      } catch (err) {
        if (isUnauthorized(err)) signOut();
        throw err;
      }
    },
    [token, signOut]
  );

  const handleReveal = useCallback(
    async (company: Company) => {
      if (!token) throw new Error('Not signed in.');
      try {
        const response = await adminClient.revealPassword(token, company.id);
        return response.password;
      } catch (err) {
        if (isUnauthorized(err)) signOut();
        throw err;
      }
    },
    [token, signOut]
  );

  if (!token) {
    return <AdminSignInForm onSignedIn={handleSignedIn} />;
  }

  const linkClass = (active: boolean) =>
    cn(
      'rounded-md px-2 transition-colors',
      active ? 'bg-sidebar-accent/60 font-medium' : 'hover:bg-sidebar-accent/30',
    );

  return (
    <div className="flex h-[calc(100vh-57px)] w-full overflow-hidden">
      <Sidebar>
        <SidebarBody className="justify-between gap-10 border-r border-sidebar-border bg-sidebar">
          <div className="flex flex-1 flex-col overflow-y-auto overflow-x-hidden">
            <div className="mb-6 flex items-center gap-2 py-2">
              <div className="flex size-8 shrink-0 items-center justify-center rounded-md bg-primary text-primary-foreground">
                <ShieldCheck className="size-4" />
              </div>
              <SidebarHeading>Camri Desk</SidebarHeading>
            </div>

            <div className="flex flex-col gap-1">
              <SidebarLink
                link={{
                  label: 'Companies',
                  href: '#companies',
                  icon: <Building2 className="size-5 shrink-0 text-neutral-700 dark:text-neutral-200" />,
                }}
                className={linkClass(category === 'companies')}
                onClick={(e) => {
                  e.preventDefault();
                  setCategory('companies');
                }}
              />
              <SidebarLink
                link={{
                  label: 'Company Requests',
                  href: '#company-requests',
                  icon: <ClipboardList className="size-5 shrink-0 text-neutral-700 dark:text-neutral-200" />,
                }}
                className={linkClass(category === 'requests')}
                onClick={(e) => {
                  e.preventDefault();
                  setCategory('requests');
                }}
              />
            </div>
          </div>

          <div>
            <SidebarLink
              link={{
                label: 'Sign out',
                href: '#signout',
                icon: <LogOut className="size-5 shrink-0 text-neutral-700 dark:text-neutral-200" />,
              }}
              className="rounded-md px-2 hover:bg-sidebar-accent/30"
              onClick={(e) => {
                e.preventDefault();
                signOut();
              }}
            />
          </div>
        </SidebarBody>
      </Sidebar>

      <main className="flex-1 overflow-y-auto px-6 py-8">
        <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-lg font-semibold leading-tight">
              {category === 'companies' ? 'Company Accounts' : 'Company Requests'}
            </h1>
            <p className="text-xs text-muted-foreground">
              {category === 'companies'
                ? 'Clients onboarded to the reconciliation platform.'
                : 'Companies that asked to be onboarded.'}
            </p>
          </div>

          {category === 'companies' && (
            <div className="flex items-center gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={refresh}
                disabled={loading}
                title="Refresh the list"
              >
                <RefreshCw className={loading ? 'size-3.5 animate-spin' : 'size-3.5'} />
                Refresh
              </Button>
              <Button
                type="button"
                size="sm"
                onClick={() => {
                  setEditTarget(null);
                  setDialogOpen(true);
                }}
                className="gap-1 bg-emerald-700 text-white hover:bg-emerald-800 dark:bg-emerald-600 dark:hover:bg-emerald-700"
              >
                <Plus className="size-4" />
                Add Companies
              </Button>
            </div>
          )}
        </div>

        {error && (
          <div className="mb-4 flex items-center gap-2 rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2 text-xs text-destructive">
            <AlertCircle className="size-4 shrink-0" /> {error}
          </div>
        )}

        {category === 'companies' ? (
          <CompaniesTable
            companies={companies}
            loading={loading}
            token={token}
            onEdit={(company) => {
              setEditTarget(company);
              setDialogOpen(true);
            }}
            onDelete={handleDelete}
            onReveal={handleReveal}
          />
        ) : (
          <CompanyRequestsTable token={token} />
        )}

        <CompanyFormDialog
          open={dialogOpen}
          onOpenChange={(open) => {
            setDialogOpen(open);
            if (!open) setEditTarget(null);
          }}
          token={token}
          company={editTarget}
          onSaved={handleSaved}
        />
      </main>
    </div>
  );
}

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
