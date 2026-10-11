/* بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */

/**
 * Membership server helpers (RSC only).
 *
 * The application is gated on a company-granted membership (FR-009). The
 * authoritative check is server-side in auth_middleware; these helpers are the
 * UX layer that keeps a no-grant account out of protected pages and sends them
 * to the subscription page. They run on the server and read the NextAuth
 * access token from the session, so the token never has to be threaded through
 * the component tree.
 */
import { redirect } from 'next/navigation';
import type { Membership } from '@/types/employee.types';
import { auth } from '@/lib/auth';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Resolve the signed-in account's accepted membership, or null when it has
 * none (or the session token is missing/invalid).
 */
export async function getMembership(token: string): Promise<Membership | null> {
  const response = await fetch(`${API_BASE_URL}/api/me/membership`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: 'no-store',
  });
  if (!response.ok) return null;
  const data = (await response.json()) as { membership: Membership | null };
  return data.membership ?? null;
}

/**
 * Require an accepted membership AND an active company free trial for a
 * protected page; redirect to the subscription page otherwise (the only surface
 * an account may reach, alongside sign-in). The backend enforces the same gate
 * in auth_middleware, so this is the UX mirror. Returns the membership.
 */
export async function requireMembership(): Promise<Membership> {
  const session = await auth();
  const token = (session?.user as { access_token?: string } | undefined)?.access_token;
  if (!token) redirect('/subscription');

  const membership = await getMembership(token);
  if (!membership || !membership.trial_active) redirect('/subscription');
  return membership;
}

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
