/* بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */

/**
 * SubscriptionPlans — the subscription layer's landing content.
 *
 * Two side-by-side package cards that fill most of the viewport. The Companies
 * card is the live path ("Employee Request"); the Individual card is
 * cherry-themed and marked coming soon. Everything except the employee request
 * dialog is deliberately inert — the company request, the individual plans and
 * the plan prices belong to later specifications.
 *
 * Sizing note: GlareCard hardcodes a 320px / 17:21 card, so `containerClassName`
 * overrides the frame (full width of the grid cell, fixed height) while
 * `className` themes the card surface.
 */
'use client';

import { useState } from 'react';
import { Building2, Check, User } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { GlareButton } from '@/components/ui/glare-button';
import { GlareCard } from '@/components/ui/glare-card';
import { CompanyRequestFlow } from '@/components/company-request/company-request-flow';
import { EmployeeRequestDialog } from '@/components/subscription/employee-request-dialog';

/**
 * Shared frame: full width of its grid cell, a tall card rather than the 17:21
 * default, and a restrained pop on hover.
 */
const CARD_FRAME =
  'w-full [aspect-ratio:auto] h-[560px] hover:scale-[1.015] transition-transform';

const COMPANY_POINTS = [
  'Reconcile as a team, not alone',
  'Company-wide reconciliation history',
  'Access granted and managed by your company',
];

const INDIVIDUAL_POINTS = [
  'No company required — just sign in',
  'Bring your own bank and ledger files',
  'Short 1-day and 30-day passes',
];

/** Secondary (non-primary) look on a dark card. */
const SECONDARY_ON_DARK =
  'h-12 w-full border-white/40 bg-white/10 text-base text-white hover:bg-white/20 hover:text-white';

export function SubscriptionPlans() {
  const [requestOpen, setRequestOpen] = useState(false);
  const [companyRequestOpen, setCompanyRequestOpen] = useState(false);

  return (
    <div className="space-y-10">
      <header className="text-center">
        <h1 className="font-heading text-3xl font-semibold sm:text-4xl">
          Reconciliation AI for Companies
        </h1>
        <p className="mt-3 text-sm text-muted-foreground sm:text-base">
          Choose how you want to reconcile.
        </p>
      </header>

      <div className="grid grid-cols-1 items-stretch gap-10 md:grid-cols-2">
        {/* ── Companies ─────────────────────────────────────────────── */}
        <GlareCard
          containerClassName={CARD_FRAME}
          className="bg-gradient-to-br from-zinc-600 via-zinc-700 to-zinc-900"
        >
          <div className="flex h-full flex-col p-8 text-white">
            <div className="flex items-center gap-2 text-xs font-medium tracking-wide text-white/70 uppercase">
              <Building2 className="size-4" /> For companies
            </div>

            <h2 className="font-heading mt-3 text-2xl font-semibold">
              Companies Reconciliation
            </h2>
            <p className="mt-2 text-sm text-white/75">
              Request access to your company and reconcile on its behalf.
            </p>

            <ul className="mt-6 space-y-3 text-sm text-white/85">
              {COMPANY_POINTS.map((point) => (
                <li key={point} className="flex items-start gap-2">
                  <Check className="mt-0.5 size-4 shrink-0" />
                  {point}
                </li>
              ))}
            </ul>

            <div className="mt-auto flex flex-col gap-3 pt-8">
              {/* Opens the full-screen cinematic onboarding flow (FR-001). */}
              <Button
                type="button"
                size="lg"
                className={SECONDARY_ON_DARK}
                onClick={() => setCompanyRequestOpen(true)}
              >
                Company Request
              </Button>
              <GlareButton onClick={() => setRequestOpen(true)}>
                Employee Request
              </GlareButton>
            </div>
          </div>
        </GlareCard>

        {/* ── Individuals ───────────────────────────────────────────── */}
        <GlareCard
          containerClassName={CARD_FRAME}
          className="bg-gradient-to-br from-rose-700 via-red-800 to-rose-950"
        >
          <div className="flex h-full flex-col p-8 text-white">
            <div className="flex items-center gap-2">
              <span className="rounded-full bg-white/15 px-2.5 py-1 text-[11px] font-semibold tracking-wide uppercase">
                Coming soon
              </span>
            </div>

            <div className="mt-4 flex items-center gap-2 text-xs font-medium tracking-wide text-white/70 uppercase">
              <User className="size-4" /> For individuals
            </div>

            <h2 className="font-heading mt-3 text-2xl font-semibold">Individual Plans</h2>
            <p className="mt-2 text-sm text-white/75">
              Reconcile your own documents without a company.
            </p>

            <ul className="mt-6 space-y-3 text-sm text-white/85">
              {INDIVIDUAL_POINTS.map((point) => (
                <li key={point} className="flex items-start gap-2">
                  <Check className="mt-0.5 size-4 shrink-0" />
                  {point}
                </li>
              ))}
            </ul>

            {/* Both plans are inert placeholders until the later specification. */}
            <div className="mt-auto flex flex-col gap-3 pt-8">
              <GlareButton className="bg-gradient-to-r from-rose-500 to-red-600">
                1 Day 300 Rs
              </GlareButton>
              <GlareButton className="bg-gradient-to-r from-rose-500 to-red-600">
                30 Days 1500 Rs
              </GlareButton>
            </div>
          </div>
        </GlareCard>
      </div>

      <EmployeeRequestDialog open={requestOpen} onOpenChange={setRequestOpen} />

      <CompanyRequestFlow
        open={companyRequestOpen}
        onClose={() => setCompanyRequestOpen(false)}
      />
    </div>
  );
}

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
