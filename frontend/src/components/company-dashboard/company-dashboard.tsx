/* بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */

/**
 * CompanyDashboard
 *
 * The company-facing surface. Holds the company session in localStorage (24
 * hours, surviving browser restarts), renders the sign-in form when there is no
 * valid session, and otherwise shows the two-section dashboard: Employees and
 * Subscription. The session is read through useSyncExternalStore so the server
 * renders "signed out" and the client re-reads after hydration.
 */
'use client';

import { useState, useSyncExternalStore } from 'react';
import { CompanySignInForm } from '@/components/company-dashboard/company-sign-in-form';
import { CompanySidebar } from '@/components/company-dashboard/company-sidebar';
import { EmployeesTable } from '@/components/company-dashboard/employees-table';
import { SubscriptionPanel } from '@/components/company-dashboard/subscription-panel';
import {
  clearCompanySession,
  getCompanySessionServerSnapshot,
  getCompanySessionSnapshot,
  setCompanySession,
  subscribeToCompanySession,
} from '@/lib/company/company-session';

type DashboardSection = 'employees' | 'subscription';

export function CompanyDashboard() {
  const session = useSyncExternalStore(
    subscribeToCompanySession,
    getCompanySessionSnapshot,
    getCompanySessionServerSnapshot,
  );
  const [section, setSection] = useState<DashboardSection>('employees');

  if (!session) {
    return <CompanySignInForm onSignedIn={setCompanySession} />;
  }

  return (
    <div className="flex h-[calc(100vh-57px)] w-full overflow-hidden">
      <CompanySidebar
        companyName={session.company.name}
        section={section}
        onSelect={setSection}
        onSignOut={clearCompanySession}
      />

      <main className="flex-1 overflow-y-auto bg-background px-6 py-8">
        <header className="mb-6">
          <h1 className="font-heading text-lg font-semibold leading-tight">
            {session.company.name}
          </h1>
          <p className="text-xs text-muted-foreground">Company dashboard</p>
        </header>

        {section === 'employees' ? (
          <EmployeesTable token={session.token} />
        ) : (
          <SubscriptionPanel token={session.token} />
        )}
      </main>
    </div>
  );
}

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
