/* بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */

/**
 * EmployeesTable — the company's associated employees, with per-row Grant,
 * Delete, and Manager actions (FR-001…FR-005, FR-019).
 *
 * Rows come from the real /api/company/employees endpoint via companyClient.
 * The single search box filters automatically by employee ID first and name
 * second, with no mode to choose (FR-002): ID matches are ranked above
 * name-only matches while the newest-first order is preserved within a rank.
 */
'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  AlertCircle,
  Check,
  Loader2,
  RefreshCw,
  Search,
  Shield,
  Trash2,
  Undo2,
  UserCheck,
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
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';
import { Switch } from '@/components/ui/switch';
import { cn } from '@/lib/utils';
import { companyClient } from '@/lib/api/companyClient';
import type { CompanyEmployee } from '@/types/employee.types';
import type { EmployeeStatus } from '@/types/company.types';

const STATUS_LABELS: Record<EmployeeStatus, string> = {
  pending: 'Pending',
  accepted: 'Granted',
  denied: 'Denied',
};

function statusClass(status: EmployeeStatus): string {
  switch (status) {
    case 'accepted':
      return 'bg-emerald-600 text-white';
    case 'denied':
      return 'border-destructive/40 bg-destructive/10 text-destructive';
    default:
      return 'border-border bg-muted text-muted-foreground';
  }
}

/** ID match → rank 0, name-only match → rank 1, no match → rank 2 (FR-002). */
function matchRank(employee: CompanyEmployee, query: string): number {
  const q = query.trim().toLowerCase();
  if (!q) return 0;
  if (employee.employee_id.toLowerCase().includes(q)) return 0;
  if (employee.employee_name.toLowerCase().includes(q)) return 1;
  return 2;
}

function describeError(err: unknown, fallback: string): string {
  return err instanceof Error && err.message ? err.message : fallback;
}

interface EmployeesTableProps {
  token: string;
}

type LoadState = 'loading' | 'ready' | 'error';

export function EmployeesTable({ token }: EmployeesTableProps) {
  const [employees, setEmployees] = useState<CompanyEmployee[]>([]);
  const [state, setState] = useState<LoadState>('loading');
  const [error, setError] = useState<string | null>(null);
  const [rowError, setRowError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [busyId, setBusyId] = useState<string | null>(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);

  // Plain fetch (no state) so the mount effect can populate state from promise
  // callbacks — no synchronous setState in the effect body.
  const fetchEmployees = useCallback(() => companyClient.listEmployees(token), [token]);

  const load = useCallback(async () => {
    if (!token) return;
    setState('loading');
    setError(null);
    try {
      const result = await fetchEmployees();
      setEmployees(result.employees);
      setState('ready');
    } catch (err) {
      setState('error');
      setError(describeError(err, 'Failed to load employees.'));
    }
  }, [fetchEmployees, token]);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    fetchEmployees()
      .then((result) => {
        if (cancelled) return;
        setEmployees(result.employees);
        setState('ready');
      })
      .catch((err) => {
        if (cancelled) return;
        setState('error');
        setError(describeError(err, 'Failed to load employees.'));
      });
    return () => {
      cancelled = true;
    };
  }, [fetchEmployees, token]);

  const visible = useMemo(() => {
    return [...employees]
      .filter((employee) => matchRank(employee, search) < 2)
      .sort((a, b) => matchRank(a, search) - matchRank(b, search));
  }, [employees, search]);

  const replaceEmployee = (updated: CompanyEmployee) => {
    setEmployees((prev) => prev.map((e) => (e.id === updated.id ? updated : e)));
  };

  const handleGrant = async (employee: CompanyEmployee) => {
    setBusyId(employee.id);
    setRowError(null);
    try {
      replaceEmployee(await companyClient.grantAccess(token, employee.id));
    } catch (err) {
      setRowError(describeError(err, 'Failed to grant access.'));
    } finally {
      setBusyId(null);
    }
  };

  const handleRevoke = async (employee: CompanyEmployee) => {
    setBusyId(employee.id);
    setRowError(null);
    try {
      replaceEmployee(await companyClient.revokeAccess(token, employee.id));
    } catch (err) {
      setRowError(describeError(err, 'Failed to revoke access.'));
    } finally {
      setBusyId(null);
    }
  };

  const handleDelete = async (employee: CompanyEmployee) => {
    if (confirmDeleteId !== employee.id) {
      setConfirmDeleteId(employee.id);
      return;
    }
    setBusyId(employee.id);
    setRowError(null);
    try {
      await companyClient.deleteEmployee(token, employee.id);
      setEmployees((prev) => prev.filter((e) => e.id !== employee.id));
      setConfirmDeleteId(null);
    } catch (err) {
      setRowError(describeError(err, 'Failed to delete the request.'));
    } finally {
      setBusyId(null);
    }
  };

  const handleToggleManager = async (employee: CompanyEmployee, next: boolean) => {
    setBusyId(employee.id);
    setRowError(null);
    try {
      replaceEmployee(await companyClient.setManager(token, employee.id, next));
    } catch (err) {
      setRowError(describeError(err, 'Failed to update the Manager role.'));
    } finally {
      setBusyId(null);
    }
  };

  if (state === 'loading' && employees.length === 0) {
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
        <p className="text-sm font-medium">Couldn&apos;t load employees</p>
        <p className="mt-0.5 text-xs text-muted-foreground">{error}</p>
        <Button type="button" size="sm" variant="outline" className="mt-4 gap-1" onClick={() => void load()}>
          <RefreshCw className="size-3" />
          Try again
        </Button>
      </div>
    );
  }

  if (employees.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-border p-10 text-center">
        <Users className="mx-auto mb-2 size-6 text-muted-foreground" />
        <p className="text-sm font-medium">No employees yet</p>
        <p className="mt-0.5 text-xs text-muted-foreground">
          Employees who request access will appear here.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="relative max-w-sm">
        <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          type="search"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Search by employee ID or name"
          aria-label="Search employees by ID or name"
          className="pl-9"
        />
      </div>

      {rowError && (
        <div className="flex items-center gap-2 rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2 text-xs text-destructive">
          <AlertCircle className="size-4 shrink-0" />
          {rowError}
        </div>
      )}

      {visible.length === 0 ? (
        <div className="rounded-lg border border-dashed border-border p-10 text-center">
          <Search className="mx-auto mb-2 size-6 text-muted-foreground" />
          <p className="text-sm font-medium">No matches</p>
          <p className="mt-0.5 text-xs text-muted-foreground">
            No employee matches &ldquo;{search.trim()}&rdquo;.
          </p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-lg border border-border">
          <Table>
            <TableHeader>
              <TableRow className="bg-muted/40">
                <TableHead>Employee</TableHead>
                <TableHead>Employee ID</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Manager</TableHead>
                <TableHead className="w-[230px] text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {visible.map((employee) => {
                const isGranted = employee.status === 'accepted';
                const isBusy = busyId === employee.id;
                const confirmingDelete = confirmDeleteId === employee.id;
                return (
                  <TableRow key={employee.id}>
                    <TableCell className="font-medium">{employee.employee_name}</TableCell>
                    <TableCell className="font-mono text-xs">{employee.employee_id}</TableCell>
                    <TableCell>
                      <Badge
                        variant="outline"
                        className={cn('border', statusClass(employee.status))}
                      >
                        {STATUS_LABELS[employee.status]}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Switch
                          checked={employee.is_manager}
                          disabled={isBusy}
                          onCheckedChange={(checked) =>
                            void handleToggleManager(employee, checked)
                          }
                          aria-label={`Toggle Manager role for ${employee.employee_name}`}
                        />
                        {employee.is_manager && (
                          <Badge variant="outline" className="gap-1 border-amber-500/40 text-amber-600">
                            <Shield className="size-3" />
                            Manager
                          </Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex justify-end gap-2">
                        {!isGranted && (
                          <Button
                            type="button"
                            size="xs"
                            variant="outline"
                            className="gap-1"
                            disabled={isBusy}
                            onClick={() => void handleGrant(employee)}
                          >
                            {isBusy ? (
                              <Loader2 className="size-3 animate-spin" />
                            ) : (
                              <UserCheck className="size-3" />
                            )}
                            Grant Access
                          </Button>
                        )}
                        {isGranted && (
                          <Button
                            type="button"
                            size="xs"
                            variant="outline"
                            className="gap-1"
                            disabled={isBusy}
                            onClick={() => void handleRevoke(employee)}
                            title="Revoke access (revert to pending)"
                          >
                            {isBusy ? (
                              <Loader2 className="size-3 animate-spin" />
                            ) : (
                              <Undo2 className="size-3" />
                            )}
                            Revoke
                          </Button>
                        )}
                        <Button
                          type="button"
                          size="xs"
                          variant={confirmingDelete ? 'destructive' : 'outline'}
                          className="gap-1"
                          disabled={isBusy}
                          onClick={() => void handleDelete(employee)}
                        >
                          {isBusy && confirmingDelete ? (
                            <Loader2 className="size-3 animate-spin" />
                          ) : confirmingDelete ? (
                            <Check className="size-3" />
                          ) : (
                            <Trash2 className="size-3" />
                          )}
                          {confirmingDelete ? 'Confirm?' : 'Delete'}
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
