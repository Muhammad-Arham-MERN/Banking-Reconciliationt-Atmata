# 🌐 Production Environment Variables

> Every variable you need to set when deploying the Bank Reconciliation System to production — frontend on **Vercel**, backend on **your cloud host**, and **Google Cloud Console**.

---

## 📦 Frontend — Vercel

Set these in **Vercel Project Settings → Environment Variables**.

| Variable | Value | Purpose |
|---|---|---|
| `AUTH_URL` | `https://yourdomain.com` | NextAuth canonical URL (must match the browser-visible domain) |
| `AUTH_GOOGLE_ID` | `1041754935818-...apps.googleusercontent.com` | Google OAuth Client ID |
| `AUTH_GOOGLE_SECRET` | `GOCSPX-...` | Google OAuth Client Secret |
| `AUTH_SECRET` | `897c78f7...665602` | HS256 signing key (shared with backend as `NEXTAUTH_SECRET`) |
| `DATABASE_URL` | `postgresql://...@cockroachlabs.cloud:26257/myCustomDB?sslmode=verify-full` | CockroachDB connection string for Auth.js adapter |
| `NEXT_PUBLIC_API_URL` | `https://your-backend-domain.com` | Backend API base URL (the frontend calls this for all API requests) |

---

## ⚙️ Backend — Your Cloud Host

Set these as environment variables on the machine / container running the FastAPI backend.

| Variable | Value | Purpose |
|---|---|---|
| `CORS_ORIGINS` | `https://yourdomain.com,https://your-app.vercel.app` | Comma-separated list of frontend origins allowed by CORS |
| `NEXTAUTH_SECRET` | `897c78f7...665602` | MUST match frontend `AUTH_SECRET` — used to verify Auth.js JWTs |
| `DATABASE_URL` | `postgresql://...@cockroachlabs.cloud:26257/myCustomDB?sslmode=require` | CockroachDB connection string (same DB the frontend uses) |

> **Tip:** `DATABASE_URL` uses `sslmode=require` on the backend (server-to-server) and `sslmode=verify-full` on Vercel (browser-backed). Both work — the difference is how strictly the TLS certificate is checked.

---

## 🔐 Google Cloud Console — OAuth Consent Screen

Add these URLs to your [Google Cloud Console](https://console.cloud.google.com/apis/credentials) OAuth 2.0 Client ID.

### Authorized JavaScript Origins

```
https://yourdomain.com
```

### Authorized Redirect URIs

```
https://yourdomain.com/api/auth/callback/google
```

All three layers — frontend `AUTH_URL`, Google's allowed redirect, and backend `CORS_ORIGINS` — must reference the **same domain** or authentication will fail.

---

## ✅ Quick Checklist

- [ ] `AUTH_URL` set on Vercel
- [ ] `NEXT_PUBLIC_API_URL` set on Vercel, pointing to backend
- [ ] `CORS_ORIGINS` set on backend, including Vercel domain
- [ ] `NEXTAUTH_SECRET` on backend matches `AUTH_SECRET` on Vercel
- [ ] `DATABASE_URL` set on both Vercel and backend
- [ ] Google OAuth credentials include the production domain
- [ ] Backend deployed and reachable at the URL in `NEXT_PUBLIC_API_URL`
