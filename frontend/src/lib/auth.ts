/** بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */
import NextAuth from "next-auth";
import PostgresAdapter from "@auth/pg-adapter";
import { Pool } from "pg";
import { authConfig } from "./auth.config";
import type { Session } from "next-auth";

const SCHEMA_SQL = `
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    email VARCHAR(255),
    "emailVerified" TIMESTAMPTZ,
    image TEXT
);
CREATE TABLE IF NOT EXISTS accounts (
    id SERIAL PRIMARY KEY,
    "userId" INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(255) NOT NULL,
    provider VARCHAR(255) NOT NULL,
    "providerAccountId" VARCHAR(255) NOT NULL,
    refresh_token TEXT,
    access_token TEXT,
    expires_at BIGINT,
    id_token TEXT,
    scope TEXT,
    session_state TEXT,
    token_type TEXT
);
CREATE TABLE IF NOT EXISTS sessions (
    id SERIAL PRIMARY KEY,
    "userId" INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires TIMESTAMPTZ NOT NULL,
    "sessionToken" VARCHAR(255) NOT NULL
);
CREATE TABLE IF NOT EXISTS verification_token (
    identifier TEXT NOT NULL,
    expires TIMESTAMPTZ NOT NULL,
    token TEXT NOT NULL,
    PRIMARY KEY (identifier, token)
);
`;

async function ensureDatabase(): Promise<Pool> {
  const dbUrl = process.env.DATABASE_URL;
  if (!dbUrl) {
    throw new Error("DATABASE_URL environment variable is required but not set");
  }
  const url = new URL(dbUrl);
  const dbName = url.pathname.replace(/^\//, "") || "defaultdb";

  // Connect without specifying a database to check/create it
  const adminUrl = new URL(url.toString());
  adminUrl.pathname = "/postgres"; // CockroachDB always has 'postgres' db
  const adminPool = new Pool({ connectionString: adminUrl.toString(), max: 1 });

  try {
    const res = await adminPool.query(
      `SELECT 1 FROM pg_database WHERE datname = $1`,
      [dbName]
    );
    if (res.rowCount === 0) {
      await adminPool.query(`CREATE DATABASE "${dbName}"`);
      console.log(`✅ Created database "${dbName}"`);
    }
  } catch {
    // Fallback: try connecting directly, database may already exist
  } finally {
    await adminPool.end();
  }

  const pool = new Pool({ connectionString: url.toString(), max: 5 });

  // Create auth adapter tables if they don't exist
  await pool.query(SCHEMA_SQL);
  console.log("✅ Auth schema tables ensured");

  return pool;
}

let _instance: {
  auth: () => Promise<Session | null>;
  handlers: { GET: (req: any) => Promise<Response>; POST: (req: any) => Promise<Response> };
  signIn: (...args: any[]) => any;
  signOut: (...args: any[]) => any;
} | null = null;
let _promise: Promise<void> | null = null;

async function getAuth() {
  if (!_promise) {
    _promise = (async () => {
      const pool = await ensureDatabase();
      const result = NextAuth({ ...authConfig, adapter: PostgresAdapter(pool) });
      _instance = {
        auth: () => result.auth() as Promise<Session | null>,
        handlers: result.handlers,
        signIn: result.signIn,
        signOut: result.signOut,
      };
    })();
  }
  await _promise;
  return _instance!;
}

export async function auth(): Promise<Session | null> {
  const instance = await getAuth();
  return instance.auth();
}

export const handlers = new Proxy({} as {
  GET: (req: any) => Promise<Response>;
  POST: (req: any) => Promise<Response>;
}, {
  get(_, prop) {
    return (...args: any[]) => getAuth().then(i => (i.handlers as any)[prop](...args));
  },
});

export const signIn = (...args: any[]) => getAuth().then(i => i.signIn(...args));
export const signOut = (...args: any[]) => getAuth().then(i => i.signOut(...args));
/** وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
