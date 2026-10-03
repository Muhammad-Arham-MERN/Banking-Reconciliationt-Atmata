/* بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */

/**
 * Admin session store.
 *
 * The admin token is held in sessionStorage — scoped to the BROWSER SESSION, so
 * closing the browser signs the Developer out (no "remember me"). sessionStorage
 * fires no event in the tab that wrote it, so this module keeps its own listener
 * set and a cached snapshot for useSyncExternalStore.
 *
 * useSyncExternalStore (rather than an effect + setState) is what lets the
 * component read sessionStorage without a hydration mismatch: the server
 * snapshot is null and the client re-reads after hydration.
 */

const TOKEN_KEY = 'camri_admin_token';

const listeners = new Set<() => void>();

let cached: string | null = null;
let cacheInitialized = false;

function readFromStorage(): string | null {
  if (typeof window === 'undefined') return null;
  try {
    return window.sessionStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

function emit() {
  for (const listener of listeners) listener();
}

export function subscribeToAdminSession(listener: () => void): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

/** Client snapshot — cached so repeated calls stay referentially stable. */
export function getAdminSessionSnapshot(): string | null {
  if (!cacheInitialized) {
    cached = readFromStorage();
    cacheInitialized = true;
  }
  return cached;
}

/** Server snapshot — always signed out, so hydration starts from a known state. */
export function getAdminSessionServerSnapshot(): string | null {
  return null;
}

export function setAdminToken(token: string | null): void {
  if (typeof window !== 'undefined') {
    try {
      if (token) window.sessionStorage.setItem(TOKEN_KEY, token);
      else window.sessionStorage.removeItem(TOKEN_KEY);
    } catch {
      // Storage unavailable (private mode) — the in-memory value still works
      // for this page view.
    }
  }
  cached = token;
  cacheInitialized = true;
  emit();
}

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
