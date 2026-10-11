/* بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */

/**
 * CompanySidebar — the company dashboard's navigation, built on the Aceternity
 * sidebar. It exposes exactly the two sections the spec allows: Employees and
 * Subscription (FR-019), plus the company's name and a sign-out action.
 */
'use client';

import { Building2, CreditCard, LogOut, Users } from 'lucide-react';
import { motion, useReducedMotion } from 'motion/react';
import {
  Sidebar,
  SidebarBody,
  SidebarLink,
  useSidebar,
} from '@/components/ui/sidebar';
import { cn } from '@/lib/utils';

type DashboardSection = 'employees' | 'subscription';

interface CompanySidebarProps {
  companyName: string;
  section: DashboardSection;
  onSelect: (section: DashboardSection) => void;
  onSignOut: () => void;
}

/** The company name, collapsing with the sidebar like the link labels. */
function SidebarHeading({ children }: { children: React.ReactNode }) {
  const { open, animate } = useSidebar();
  const reduceMotion = useReducedMotion();
  return (
    <motion.span
      animate={{
        display: animate ? (open ? 'inline-block' : 'none') : 'inline-block',
        opacity: animate ? (open ? 1 : 0) : 1,
      }}
      transition={reduceMotion ? { duration: 0 } : undefined}
      className="truncate text-sm font-semibold"
    >
      {children}
    </motion.span>
  );
}

export function CompanySidebar({
  companyName,
  section,
  onSelect,
  onSignOut,
}: CompanySidebarProps) {
  const linkClass = (active: boolean) =>
    cn(
      'rounded-md px-2 transition-colors',
      active ? 'bg-sidebar-accent/60 font-medium' : 'hover:bg-sidebar-accent/30',
    );

  return (
    <Sidebar>
      <SidebarBody className="justify-between gap-10 border-r border-sidebar-border bg-sidebar">
        <div className="flex flex-1 flex-col overflow-y-auto overflow-x-hidden">
          <div className="mb-6 flex items-center gap-2 py-2">
            <div className="flex size-8 shrink-0 items-center justify-center rounded-md bg-primary text-primary-foreground">
              <Building2 className="size-4" />
            </div>
            <SidebarHeading>{companyName}</SidebarHeading>
          </div>

          <div className="flex flex-col gap-1">
            <SidebarLink
              link={{
                label: 'Employees',
                href: '#employees',
                icon: <Users className="size-5 shrink-0 text-neutral-700 dark:text-neutral-200" />,
              }}
              className={linkClass(section === 'employees')}
              onClick={(e) => {
                e.preventDefault();
                onSelect('employees');
              }}
            />
            <SidebarLink
              link={{
                label: 'Subscription',
                href: '#subscription',
                icon: <CreditCard className="size-5 shrink-0 text-neutral-700 dark:text-neutral-200" />,
              }}
              className={linkClass(section === 'subscription')}
              onClick={(e) => {
                e.preventDefault();
                onSelect('subscription');
              }}
            />
          </div>
        </div>

        <div>
          <SidebarLink
            link={{
              label: 'Sign out',
              href: '#signout',
              icon: <LogOut className="size-5 shrink-0 text-neutral-700 dark:text-neutral-200" />,
            }}
            className="rounded-md px-2 hover:bg-sidebar-accent/30"
            onClick={(e) => {
              e.preventDefault();
              onSignOut();
            }}
          />
        </div>
      </SidebarBody>
    </Sidebar>
  );
}

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
