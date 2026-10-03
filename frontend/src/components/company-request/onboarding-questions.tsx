/* بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */

/**
 * OnboardingQuestions — the four steps of the Company Request flow, shown one at
 * a time with a fade (FR-007). Each step is gated by its format check (FR-008);
 * the final step captures the contact details (email + phone together). Advancing
 * notifies the parent so it can play the boss's hands-up pose (FR-009).
 */
'use client';

import { useState } from 'react';
import { AnimatePresence, motion, useReducedMotion } from 'motion/react';
import { ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  validateCompanyName,
  validateEmail,
  validatePhone,
  validateRole,
  validateWebsiteSocials,
} from '@/lib/company/company-validation';

export interface OnboardingAnswers {
  company_name: string;
  role: string;
  website_socials: string;
  email: string;
  phone: string;
}

interface OnboardingQuestionsProps {
  /** Called when the visitor advances (so the boss can raise the pen). */
  onAdvance: () => void;
  /** Called with the collected answers after the final step. */
  onComplete: (answers: OnboardingAnswers) => void;
  /** True while the parent is persisting the request (final step). */
  submitting?: boolean;
  /** A submission failure from the parent, distinct from step validation. */
  submitError?: string | null;
}

type StepId = 'companyName' | 'role' | 'websiteSocials' | 'contact';

const STEPS: { id: StepId; title: string; hint: string }[] = [
  { id: 'companyName', title: 'What is your company called?', hint: 'The name you go by.' },
  { id: 'role', title: 'What does your company do?', hint: 'A short line on what you serve.' },
  { id: 'websiteSocials', title: 'Where can we find you online?', hint: 'A website or a social handle.' },
  { id: 'contact', title: 'How do we reach your team?', hint: 'Email and phone number.' },
];

export function OnboardingQuestions({
  onAdvance,
  onComplete,
  submitting = false,
  submitError = null,
}: OnboardingQuestionsProps) {
  const reduceMotion = useReducedMotion();
  const [stepIndex, setStepIndex] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const [companyName, setCompanyName] = useState('');
  const [role, setRole] = useState('');
  const [websiteSocials, setWebsiteSocials] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');

  const step = STEPS[stepIndex];
  const isLast = stepIndex === STEPS.length - 1;

  const handleNext = () => {
    // Validate the current step only; the others were validated when advanced.
    if (step.id === 'companyName') {
      const result = validateCompanyName(companyName);
      if (!result.valid) return setError(result.message ?? 'Enter your company name.');
    }
    if (step.id === 'role') {
      const result = validateRole(role);
      if (!result.valid) return setError(result.message ?? 'Tell us what your company does.');
    }
    if (step.id === 'websiteSocials') {
      const result = validateWebsiteSocials(websiteSocials);
      if (!result.valid) return setError(result.message ?? 'Add a website or handle.');
    }
    if (step.id === 'contact') {
      const emailResult = validateEmail(email);
      if (!emailResult.valid) return setError(emailResult.message ?? 'Enter a valid email.');
      const phoneResult = validatePhone(phone);
      if (!phoneResult.valid) return setError(phoneResult.message ?? 'Enter a valid phone number.');
    }

    setError(null);

    if (isLast) {
      onComplete({
        company_name: companyName.trim(),
        role: role.trim(),
        website_socials: websiteSocials.trim(),
        email: email.trim(),
        phone: phone.trim(),
      });
      return;
    }

    setStepIndex((index) => index + 1);
    onAdvance();
  };

  return (
    <div className="mx-auto w-full max-w-lg">
      <AnimatePresence mode="wait">
        <motion.div
          key={step.id}
          initial={reduceMotion ? false : { opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          exit={reduceMotion ? { opacity: 0 } : { opacity: 0, y: -18 }}
          transition={
            reduceMotion
              ? { duration: 0 }
              : { duration: 0.4, ease: [0.22, 1, 0.36, 1] }
          }
          className="rounded-3xl border border-white/12 p-8 text-white"
        >
          <p className="text-[11px] font-medium uppercase tracking-[0.2em] text-white/50">
            Step {stepIndex + 1} of {STEPS.length}
          </p>
          <h2 className="font-heading mt-2 text-2xl font-semibold sm:text-3xl">{step.title}</h2>
          <p className="mt-2 text-sm text-white/60">{step.hint}</p>

          {(error || submitError) && (
            <p className="mt-4 rounded-md border border-red-400/40 bg-red-500/10 px-3 py-2 text-xs text-red-200">
              {error ?? submitError}
            </p>
          )}

          <div className="mt-6 space-y-4">
            {step.id === 'companyName' && (
              <Input
                autoFocus
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                placeholder="e.g. Greaves Pakistan"
                className="h-11 border-white/25 bg-white/5 text-white placeholder:text-white/40"
                onKeyDown={(e) => e.key === 'Enter' && handleNext()}
              />
            )}

            {step.id === 'role' && (
              <Input
                autoFocus
                value={role}
                onChange={(e) => setRole(e.target.value)}
                placeholder="e.g. Textile manufacturing and export"
                className="h-11 border-white/25 bg-white/5 text-white placeholder:text-white/40"
                onKeyDown={(e) => e.key === 'Enter' && handleNext()}
              />
            )}

            {step.id === 'websiteSocials' && (
              <Input
                autoFocus
                value={websiteSocials}
                onChange={(e) => setWebsiteSocials(e.target.value)}
                placeholder="acme.com or @acme"
                className="h-11 border-white/25 bg-white/5 text-white placeholder:text-white/40"
                onKeyDown={(e) => e.key === 'Enter' && handleNext()}
              />
            )}

            {step.id === 'contact' && (
              <>
                <Input
                  autoFocus
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@company.com"
                  className="h-11 border-white/25 bg-white/5 text-white placeholder:text-white/40"
                />
                <Input
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="+92 300 1234567"
                  className="h-11 border-white/25 bg-white/5 text-white placeholder:text-white/40"
                  onKeyDown={(e) => e.key === 'Enter' && handleNext()}
                />
              </>
            )}
          </div>

          <Button
            type="button"
            onClick={handleNext}
            disabled={submitting}
            className="mt-7 w-full gap-2"
          >
            {submitting ? 'Sending…' : isLast ? 'Send Request' : 'Next'}
            <ArrowRight className="size-4" />
          </Button>
        </motion.div>
      </AnimatePresence>
    </div>
  );
}

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
