/* بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */

/**
 * SubscriptionPanel — the company dashboard's Subscription section.
 *
 * Shows the free-trial window the Developer assigned from the Admin Dashboard
 * and lets the company activate it with a Start button. Starting is what
 * unlocks the application for the company's employees: until the trial is
 * active, every employee is refused (see auth_middleware's trial gate).
 * Billing itself belongs to a later specification.
 */
'use client';

import { useCallback, useEffect, useState } from 'react';
import {
  AlertCircle,
  CalendarDays,
  CheckCircle2,
  Clock,
  Loader2,
  Sparkles,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { companyClient } from '@/lib/api/companyClient';
import type { CompanyTrialState } from '@/types/company.types';

/** ISO date → "15 Jan 2026" (local, no timezone shift). */
function formatIsoDate(value: string | null): string {
  if (!value) return '—';
  const [y, m, d] = value.split('-').map(Number);
  return new Date(y, (m ?? 1) - 1, d ?? 1).toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
}

interface SubscriptionPanelProps {
  token: string;
}

type LoadState = 'loading' | 'ready' | 'error';

export function SubscriptionPanel({ token }: SubscriptionPanelProps) {
  const [trial, setTrial] = useState<CompanyTrialState | null>(null);
  const [state, setState] = useState<LoadState>('loading');
  const [error, setError] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);

  const load = useCallback(async () => {
    if (!token) return;
    setState('loading');
    setError(null);
    try {
      setTrial(await companyClient.getTrial(token));
      setState('ready');
    } catch (err) {
      setState('error');
      setError(err instanceof Error ? err.message : 'Failed to load the free trial.');
    }
  }, [token]);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    companyClient
      .getTrial(token)
      .then((result) => {
        if (cancelled) return;
        setTrial(result);
        setState('ready');
      })
      .catch((err) => {
        if (cancelled) return;
        setState('error');
        setError(err instanceof Error ? err.message : 'Failed to load the free trial.');
      });
    return () => {
      cancelled = true;
    };
  }, [token]);

  const handleStart = async () => {
    setStarting(true);
    setError(null);
    try {
      setTrial(await companyClient.startTrial(token));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start the free trial.');
    } finally {
      setStarting(false);
    }
  };

  const window =
    trial?.trial_from && trial?.trial_to
      ? `${formatIsoDate(trial.trial_from)} → ${formatIsoDate(trial.trial_to)}`
      : null;

  return (
    <div className="max-w-md">
      <Card className={trial?.status === 'active' ? 'border-emerald-500/40' : 'border-dashed'}>
        <CardHeader>
          <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
            <Sparkles className="size-4" /> Subscription
          </div>
          <CardTitle className="mt-2 text-lg">Free trial</CardTitle>
          <CardDescription>
            Unlock the full reconciliation workflow for your whole team.
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-4">
          {state === 'loading' && (
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Loader2 className="size-3.5 animate-spin" /> Loading your free trial…
            </div>
          )}

          {error && (
            <div className="flex items-start gap-2 rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2 text-xs text-destructive">
              <AlertCircle className="mt-0.5 size-4 shrink-0" />
              <div className="space-y-2">
                <p>{error}</p>
                {state === 'error' && (
                  <Button type="button" size="xs" variant="outline" onClick={() => void load()}>
                    Try again
                  </Button>
                )}
              </div>
            </div>
          )}

          {state === 'ready' && trial && (
            <>
              {trial.status === 'not_assigned' && (
                <p className="text-xs text-muted-foreground">
                  No free trial has been assigned to your company yet. Once it is,
                  you&apos;ll be able to start it here.
                </p>
              )}

              {(trial.status === 'not_started' || trial.status === 'scheduled') && (
                <>
                  {window && (
                    <div className="flex items-center gap-2 text-sm">
                      <CalendarDays className="size-4 text-muted-foreground" />
                      <span className="font-medium">{window}</span>
                    </div>
                  )}
                  <p className="text-xs text-muted-foreground">
                    {trial.status === 'scheduled'
                      ? 'Your trial is active but its start date is still ahead — employees unlock on that date.'
                      : 'Starting begins your free-trial access. Your employees can use the application once it is active.'}
                  </p>
                  <Button
                    type="button"
                    className="w-full gap-2 bg-emerald-700 text-white hover:bg-emerald-800 dark:bg-emerald-600 dark:hover:bg-emerald-700"
                    onClick={() => void handleStart()}
                    disabled={starting}
                  >
                    {starting ? (
                      <Loader2 className="size-4 animate-spin" />
                    ) : (
                      <CheckCircle2 className="size-4" />
                    )}
                    Start free trial
                  </Button>
                </>
              )}

              {trial.status === 'active' && (
                <>
                  <Badge variant="outline" className="border-emerald-500/40 bg-emerald-500/10 text-emerald-700 dark:text-emerald-400">
                    Active
                  </Badge>
                  {window && (
                    <div className="flex items-center gap-2 text-sm">
                      <CalendarDays className="size-4 text-muted-foreground" />
                      <span className="font-medium">{window}</span>
                    </div>
                  )}
                  <p className="text-xs text-muted-foreground">
                    Active until {formatIsoDate(trial.trial_to)}. Your team has full access.
                  </p>
                </>
              )}

              {trial.status === 'expired' && (
                <>
                  <Badge variant="outline" className="gap-1 border-destructive/40 bg-destructive/10 text-destructive">
                    <Clock className="size-3" /> Expired
                  </Badge>
                  {window && (
                    <div className="flex items-center gap-2 text-sm">
                      <CalendarDays className="size-4 text-muted-foreground" />
                      <span className="font-medium">{window}</span>
                    </div>
                  )}
                  <p className="text-xs text-muted-foreground">
                    This free trial ended on {formatIsoDate(trial.trial_to)}. Ask for a new
                    trial or subscribe to restore access.
                  </p>
                </>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
