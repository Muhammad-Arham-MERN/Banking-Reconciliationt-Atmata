/* بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */

/**
 * AdminSignInForm
 *
 * The gate in front of the hidden AdminDashAccess route. Credentials are sent
 * to POST /api/admin/login and compared server-side against the backend
 * environment values — they are never bundled into the client. The returned
 * admin token is handed to the parent, which stores it for the browser session.
 */
'use client';

import React, { useState } from 'react';
import { AlertCircle, Loader2, LockKeyhole, ShieldCheck } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { adminClient } from '@/lib/api/adminClient';

interface AdminSignInFormProps {
  /** Called with the admin token after a successful sign-in. */
  onSignedIn: (token: string) => void;
}

export function AdminSignInForm({ onSignedIn }: AdminSignInFormProps) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canSubmit = username.trim().length > 0 && password.length > 0 && !submitting;

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!canSubmit) return;

    setSubmitting(true);
    setError(null);
    try {
      const result = await adminClient.login(username.trim(), password);
      setPassword('');
      onSignedIn(result.token);
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
    <div className="flex min-h-[70vh] items-center justify-center px-4 py-10">
      <div className="w-full max-w-sm rounded-xl border border-border bg-card p-6 shadow-sm">
        <div className="mb-5 flex items-center gap-2">
          <ShieldCheck className="size-5 text-primary" />
          <div>
            <h1 className="text-base font-semibold leading-tight">Admin Access</h1>
            <p className="text-xs text-muted-foreground">
              Restricted area. Authorized personnel only.
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
              htmlFor="admin-username"
              className="mb-1 block text-xs font-medium text-muted-foreground"
            >
              Username
            </label>
            <Input
              id="admin-username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
              autoFocus
              className="h-9 text-sm"
              disabled={submitting}
            />
          </div>

          <div>
            <label
              htmlFor="admin-password"
              className="mb-1 block text-xs font-medium text-muted-foreground"
            >
              Password
            </label>
            <Input
              id="admin-password"
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
