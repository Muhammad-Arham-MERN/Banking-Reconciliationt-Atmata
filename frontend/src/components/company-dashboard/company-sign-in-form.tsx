/* بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */

/**
 * CompanySignInForm
 *
 * The gate in front of the Company Dashboard. Name and password are sent to
 * POST /api/company/login and checked server-side against the company record the
 * Developer created in the Admin Dashboard. A failed attempt shows one generic
 * message — the API never discloses which field was wrong.
 */
'use client';

import React, { useState } from 'react';
import { AlertCircle, Building2, Loader2, LockKeyhole } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { companyClient } from '@/lib/api/companyClient';
import type { CompanySession } from '@/types/company.types';

interface CompanySignInFormProps {
  /** Called with the established session after a successful sign-in. */
  onSignedIn: (session: CompanySession) => void;
}

export function CompanySignInForm({ onSignedIn }: CompanySignInFormProps) {
  const [companyName, setCompanyName] = useState('');
  const [password, setPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canSubmit = companyName.trim().length > 0 && password.length > 0 && !submitting;

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!canSubmit) return;

    setSubmitting(true);
    setError(null);
    try {
      const result = await companyClient.login(companyName.trim(), password);
      setPassword('');
      onSignedIn({
        token: result.token,
        company: result.company,
        expires_at: result.expires_at,
      });
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Sign in failed. Please check your credentials.'
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-[75vh] items-center justify-center px-4 py-10">
      <div className="w-full max-w-sm rounded-xl border border-border bg-card p-6 shadow-sm">
        <div className="mb-5 flex items-center gap-2">
          <Building2 className="size-5 text-primary" />
          <div>
            <h1 className="text-base font-semibold leading-tight">Company Sign In</h1>
            <p className="text-xs text-muted-foreground">
              Enter the name and password your account manager provided.
            </p>
          </div>
        </div>

        {error && (
          <div className="mb-4 flex items-center gap-2 rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2 text-xs text-destructive">
            <AlertCircle className="size-4 shrink-0" /> {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label
              htmlFor="company-name"
              className="mb-1 block text-xs font-medium text-muted-foreground"
            >
              Company Name
            </label>
            <Input
              id="company-name"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              autoComplete="organization"
              autoFocus
              className="h-9 text-sm"
              disabled={submitting}
            />
          </div>

          <div>
            <label
              htmlFor="company-password"
              className="mb-1 block text-xs font-medium text-muted-foreground"
            >
              Password
            </label>
            <Input
              id="company-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              className="h-9 text-sm"
              disabled={submitting}
            />
          </div>

          <Button type="submit" disabled={!canSubmit} className="w-full">
            {submitting ? (
              <>
                <Loader2 className="size-4 animate-spin" /> Signing in…
              </>
            ) : (
              <>
                <LockKeyhole className="size-4" /> Sign in
              </>
            )}
          </Button>
        </form>
      </div>
    </div>
  );
}

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
