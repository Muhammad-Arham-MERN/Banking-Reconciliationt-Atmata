/* بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */

/**
 * Company session store.
 *
 * The company session (token + identity + 24-hour expiry) is held in
 * localStorage so it SURVIVES BROWSER RESTARTS — the clarified lifetime for the
 * company dashboard (the admin session uses sessionStorage instead, by contrast).
 * An entry whose `expires_at` is in the past is treated as signed out and cleared
 * on read, so the 24-hour rule is enforced without a timer.
 *
 * localStorage fires no event in the tab that wrote it, so this module keeps its
 * own listener set and a cached snapshot for useSyncExternalStore — the same
 * hydration-safe pattern as frontend/src/lib/admin/admin-session.ts.
 */
import type { CompanySession } from '@/types/company.types';

const SESSION_KEY = 'camri_company_session';

const listeners = new Set<() => void>();

let cachedSession: CompanySession | null = null;
let cacheInitialized = false;

function parseSession(raw: string | null): CompanySession | null {
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as CompanySession;
    if (!parsed || !parsed.token || !parsed.company || !parsed.expires_at) {
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

/** True when the session has no usable expiry or it has already passed. */
function isExpired(session: CompanySession): boolean {
  const at = Date.parse(session.expires_at);
  return Number.isNaN(at) ? true : at <= Date.now();
}

function readFromStorage(): CompanySession | null {
  if (typeof window === 'undefined') return null;
  try {
    const session = parseSession(window.localStorage.getItem(SESSION_KEY));
    if (session && isExpired(session)) {
      window.localStorage.removeItem(SESSION_KEY);
      return null;
    }
    return session;
  } catch {
    return null;
  }
}

function emit() {
  for (const listener of listeners) listener();
}

export function subscribeToCompanySession(listener: () => void): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

/** Client snapshot — cached so repeated calls stay referentially stable. */
export function getCompanySessionSnapshot(): CompanySession | null {
  if (!cacheInitialized) {
    cachedSession = readFromStorage();
    cacheInitialized = true;
  }
  return cachedSession;
}

/** Server snapshot — always signed out, so hydration starts from a known state. */
export function getCompanySessionServerSnapshot(): CompanySession | null {
  return null;
}

/** Persist a new company session (after a successful sign-in). */
export function setCompanySession(session: CompanySession): void {
  const raw = JSON.stringify(session);
  if (typeof window !== 'undefined') {
    try {
      window.localStorage.setItem(SESSION_KEY, raw);
    } catch {
      // Storage unavailable (private mode) — the in-memory value still works
      // for this page view.
    }
  }
  cachedSession = session;
  cacheInitialized = true;
  emit();
}

/** Drop the company session (explicit sign-out, or any 401 from the API). */
export function clearCompanySession(): void {
  if (typeof window !== 'undefined') {
    try {
      window.localStorage.removeItem(SESSION_KEY);
    } catch {
      // Ignore — the in-memory value is cleared below regardless.
    }
  }
  cachedSession = null;
  cacheInitialized = true;
  emit();
}

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
