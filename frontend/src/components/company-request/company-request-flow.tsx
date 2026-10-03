/* بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */

/**
 * CompanyRequestFlow — the full-screen "Company Request" onboarding overlay.
 *
 * A small phase machine drives the whole experience (FR-001):
 *   intro     cinematic block → stars → building → window entry
 *   questions the boss appears centred in a straight pose for a beat, then
 *             raises his arm to his cheek as the form slides in from the right
 *             and he slides left; the four fading steps follow
 *   success   the boss smiles, then the typewriter writes the confirmation
 *
 * The overlay can be dismissed at any time with the top-right cross (FR-013)
 * and fades out automatically fifteen seconds after the success message begins
 * (FR-012). On completion the collected answers are POSTed to
 * /api/company-requests (FR-006); the cinematic success message plays only once
 * the request is stored, and a failure keeps the form up so it can be retried.
 */
'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { useSession } from 'next-auth/react';
import { AnimatePresence, motion, useReducedMotion } from 'motion/react';
import { X } from 'lucide-react';
import { CinematicIntro } from './cinematic-intro';
import { OnboardingQuestions, type OnboardingAnswers } from './onboarding-questions';
import { RequestSuccess } from './request-success';
import { BossLoader, type BossMode } from './boss-loader';
import { companyRequestClient } from '@/lib/api/companyRequestClient';

type FlowPhase = 'intro' | 'questions' | 'success';

interface CompanyRequestFlowProps {
  open: boolean;
  onClose: () => void;
}

/** How long the automatic fade-out waits after the success message begins —
 * long enough for the write-on to finish and be read (FR-012). */
const AUTO_CLOSE_MS = 15000;
/** A beat to let the boss's final smile read before the animation clears. */
const SMILE_HOLD_MS = 1200;
/** How long the "hands up" pose stays before returning to idle tapping. */
const HANDS_UP_MS = 800;
/** How long the boss sits straight and centred before the form is revealed. */
const MAN_HOLD_MS = 3000;

export function CompanyRequestFlow({ open, onClose }: CompanyRequestFlowProps) {
  const { data: session } = useSession();
  const token = (session?.user as { access_token?: string } | undefined)?.access_token ?? '';
  const reduceMotion = useReducedMotion();

  const [phase, setPhase] = useState<FlowPhase>('intro');
  const [bossMode, setBossMode] = useState<BossMode>('idle');
  // False while the boss is centred in his straight pose; true once he has
  // raised his arm and the form has slid in.
  const [settled, setSettled] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const handsUpTimer = useRef<number | null>(null);
  const smileTimer = useRef<number | null>(null);

  // Start from the top every time the overlay opens. Done during render (before
  // paint) so it cannot cascade an extra render — the same pattern as
  // EmployeeRequestDialog.
  const [seededOpen, setSeededOpen] = useState<boolean | null>(null);
  if (open !== seededOpen) {
    setSeededOpen(open);
    if (open) {
      setPhase('intro');
      setBossMode('idle');
      setSettled(false);
      setSubmitting(false);
      setSubmitError(null);
    }
  }

  // Escape closes, matching the cross.
  useEffect(() => {
    if (!open) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [open, onClose]);

  // Clear pending timers on unmount.
  useEffect(
    () => () => {
      if (handsUpTimer.current) window.clearTimeout(handsUpTimer.current);
      if (smileTimer.current) window.clearTimeout(smileTimer.current);
    },
    [],
  );

  // The success message auto-fades five seconds after it begins.
  useEffect(() => {
    if (phase !== 'success') return;
    const id = window.setTimeout(onClose, AUTO_CLOSE_MS);
    return () => window.clearTimeout(id);
  }, [phase, onClose]);

  // Hold the boss centred in his straight pose for MAN_HOLD_MS, then reveal the
  // form — he lifts his arm to his cheek and slides left as it slides in.
  // Reduced motion skips the hold. A timer (not a synchronous setState) keeps
  // this effect free of cascading renders.
  useEffect(() => {
    if (phase !== 'questions') return;
    const id = window.setTimeout(() => setSettled(true), reduceMotion ? 0 : MAN_HOLD_MS);
    return () => window.clearTimeout(id);
  }, [phase, reduceMotion]);

  const handleAdvance = useCallback(() => {
    setBossMode('handsUp');
    if (handsUpTimer.current) window.clearTimeout(handsUpTimer.current);
    handsUpTimer.current = window.setTimeout(() => setBossMode('idle'), HANDS_UP_MS);
  }, []);

  const handleIntroComplete = useCallback(() => setPhase('questions'), []);

  const handleComplete = useCallback(
    async (answers: OnboardingAnswers) => {
      if (!token) {
        setSubmitError('Your session has expired. Please sign in again.');
        return;
      }
      setSubmitting(true);
      setSubmitError(null);
      try {
        await companyRequestClient.createCompanyRequest(token, answers);
        // Stored (and the Developer notified best-effort): the boss smiles,
        // then the animation clears into the success message.
        setBossMode('smile');
        smileTimer.current = window.setTimeout(() => setPhase('success'), SMILE_HOLD_MS);
      } catch (err) {
        setSubmitError(err instanceof Error ? err.message : 'Failed to send the request.');
      } finally {
        setSubmitting(false);
      }
    },
    [token],
  );

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[200] overflow-hidden bg-[radial-gradient(circle_at_50%_32%,#3a0a13_0%,#1b050a_58%,#090203_100%)]">
      {/* Skip / dismiss at any point (FR-013). */}
      <button
        type="button"
        onClick={onClose}
        aria-label="Skip and close"
        className="absolute right-5 top-5 z-[210] rounded-full bg-black/25 p-2 text-white transition hover:bg-black/45"
      >
        <X className="size-5" />
      </button>

      {phase === 'intro' && <CinematicIntro onComplete={handleIntroComplete} />}

      {phase === 'questions' && (
        <div className="absolute inset-0 flex flex-row items-center justify-center gap-6 px-6 sm:gap-12 sm:px-12">
          {/* The boss: centred and upright for a beat, then slides left as the
              form arrives (his arm lifts to his cheek via the pose change). */}
          <motion.div
            layout
            transition={
              reduceMotion
                ? { duration: 0 }
                : { duration: 0.85, ease: [0.22, 1, 0.36, 1] }
            }
            className="h-[48vh] max-h-[520px] w-[40vw] max-w-[520px] shrink-0"
          >
            <BossLoader mode={settled ? bossMode : 'straight'} className="h-full w-full" />
          </motion.div>

          {/* The information, sliding in from the right once he has settled. */}
          <AnimatePresence>
            {settled && (
              <motion.div
                key="request-form"
                initial={reduceMotion ? { opacity: 0 } : { opacity: 0, x: 90 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0 }}
                transition={
                  reduceMotion
                    ? { duration: 0 }
                    : { duration: 0.8, ease: [0.22, 1, 0.36, 1], delay: 0.05 }
                }
                className="w-full max-w-lg"
              >
                <OnboardingQuestions
                  onAdvance={handleAdvance}
                  onComplete={handleComplete}
                  submitting={submitting}
                  submitError={submitError}
                />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}

      {phase === 'success' && (
        <div className="absolute inset-0 flex items-center justify-center">
          <RequestSuccess />
        </div>
      )}
    </div>
  );
}

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
