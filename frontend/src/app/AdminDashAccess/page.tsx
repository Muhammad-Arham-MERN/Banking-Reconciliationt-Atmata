/* بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */

/**
 * AdminDashAccess — the hidden admin route.
 *
 * Not linked from anywhere in the application; reachable only by typing the
 * address directly. It deliberately does NOT use the app's NextAuth guard
 * (`auth() -> redirect("/")`) because the admin is not a NextAuth user — the
 * gate here is the sign-in form plus the admin token.
 */
import type { Metadata } from 'next';
import { AdminDashboard } from '@/components/admin/admin-dashboard';

export const dynamic = 'force-dynamic';

export const metadata: Metadata = {
  title: 'Admin Access',
  robots: { index: false, follow: false },
};

export default function AdminDashAccessPage() {
  return <AdminDashboard />;
}

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
