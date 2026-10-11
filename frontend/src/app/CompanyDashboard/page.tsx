/** بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */

/**
 * CompanyDashboard route.
 *
 * The company signs in client-side (the session lives in localStorage), so this
 * is a thin shell rather than a server-guarded page. It is NOT linked from the
 * application navigation — the Developer gives companies the address.
 */
import type { Metadata } from 'next';
import { CompanyDashboard } from '@/components/company-dashboard/company-dashboard';

export const dynamic = 'force-dynamic';

export const metadata: Metadata = {
  title: 'Company Dashboard',
  robots: { index: false, follow: false },
};

export default function CompanyDashboardPage() {
  return <CompanyDashboard />;
}

/** وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
