/* بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */

/**
 * CinematicIntro — the opening sequence of the Company Request overlay (FR-002
 * to FR-005): a cherry block slides in and covers the screen, stars streak from
 * the centre toward the viewer, a company building grows as if the camera is
 * flying toward it, then the camera zooms INTO one of the building's windows
 * (the scale origin sits on that window) until it fills the view and fades to
 * black — as if we stepped through the glass.
 *
 * The motion-heavy sequence is skipped entirely under the reduced-motion
 * preference (FR-014) — the parent is told to continue straight to the
 * questions.
 */
'use client';

import { useEffect, useState } from 'react';
import { motion, useReducedMotion } from 'motion/react';
import { CompanyBuilding } from './company-building';
import { StarField } from './star-field';

type IntroPhase = 'cover' | 'fly' | 'enter';

/**
 * The centre of one window in the building's own 220x340 viewBox (grid column 3,
 * row 5: x = 40 + 2*38 + 12, y = 50 + 4*30 + 9), expressed as a percentage so
 * the zoom converges on that pane.
 */
const ENTER_WINDOW_ORIGIN = '58.2% 52.6%';

interface CinematicIntroProps {
  /** Called once the whole sequence has finished (or was skipped). */
  onComplete: () => void;
}

export function CinematicIntro({ onComplete }: CinematicIntroProps) {
  const reduceMotion = useReducedMotion();
  const [phase, setPhase] = useState<IntroPhase>('cover');

  useEffect(() => {
    if (reduceMotion) onComplete();
  }, [reduceMotion, onComplete]);

  if (reduceMotion) return null;

  return (
    <div className="absolute inset-0 overflow-hidden bg-[radial-gradient(circle_at_50%_32%,#3a0a13_0%,#1b050a_58%,#090203_100%)]">
      {/* Cherry block slides in and settles with a motion-blur feel. */}
      <motion.div
        className="absolute inset-0 bg-[radial-gradient(circle_at_50%_32%,#3a0a13_0%,#1b050a_58%,#090203_100%)]"
        initial={{ x: '-100%', filter: 'blur(14px)' }}
        animate={{ x: 0, filter: 'blur(0px)' }}
        transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
        onAnimationComplete={() => setPhase((prev) => (prev === 'cover' ? 'fly' : prev))}
      />

      {phase !== 'cover' && (
        <>
          <StarField />

          <div className="absolute inset-0 flex items-center justify-center">
            <motion.div
              className="h-[34vmin] w-[22vmin]"
              style={{ transformOrigin: ENTER_WINDOW_ORIGIN }}
              initial={{ scale: 0.25, opacity: 0.9 }}
              animate={
                phase === 'enter'
                  ? { scale: 20, opacity: [1, 1, 0] }
                  : { scale: 1.5, opacity: 1 }
              }
              transition={
                phase === 'enter'
                  ? {
                      // Accelerate the zoom into the window…
                      scale: { duration: 1.15, ease: [0.5, 0, 0.75, 0] },
                      // …then fade once the pane has filled the view.
                      opacity: { duration: 1.15, ease: 'easeIn', times: [0, 0.55, 1] },
                    }
                  : { duration: 5, ease: 'easeIn' }
              }
              onAnimationComplete={() => {
                if (phase === 'fly') setPhase('enter');
                else if (phase === 'enter') onComplete();
              }}
            >
              <CompanyBuilding className="h-full w-full drop-shadow-2xl" />
            </motion.div>
          </div>
        </>
      )}
    </div>
  );
}

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
