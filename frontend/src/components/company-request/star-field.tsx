/* بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */

/**
 * StarField — light beams that spawn behind the company building and stream
 * outward toward the screen.
 *
 * Each beam begins at the centre (hidden behind the building), then travels
 * outward and grows — both its length and its thickness scale up as it
 * approaches the viewer, so it reads as flying forward through the light.
 * Beams are evenly spaced around the circle (not randomised) and staggered in
 * time so the flow is continuous.
 */
'use client';

import { useMemo } from 'react';
import { motion, useReducedMotion } from 'motion/react';
import { cn } from '@/lib/utils';

interface StarFieldProps {
  className?: string;
  /** Number of beams around the circle. */
  count?: number;
}

/** How far a beam reaches at full size. */
const MAX_LENGTH = 90; // vmax

/** How long one beam takes to travel from the centre to its full length. */
const CYCLE_SECONDS = 1.9;

export function StarField({ className, count = 56 }: StarFieldProps) {
  const reduceMotion = useReducedMotion();

  const beams = useMemo(
    () =>
      Array.from({ length: count }, (_, index) => ({
        // Evenly spaced around the circle — a regular fan, no randomness.
        angle: (index / count) * 360,
        // Stagger the phases so the field is full from the first frame and the
        // stream never pulses.
        delay: -(index / count) * CYCLE_SECONDS,
        key: `beam-${index}`,
      })),
    [count],
  );

  return (
    <div className={cn('pointer-events-none absolute inset-0 overflow-hidden', className)}>
      {beams.map((beam) => (
        <motion.span
          key={beam.key}
          className="absolute left-1/2 top-1/2 h-[1.6px] rounded-full"
          style={{
            width: `${MAX_LENGTH}vmax`,
            transformOrigin: '0 50%',
            rotate: `${beam.angle}deg`,
            // Fades in from the centre so the spawn point stays hidden.
            backgroundImage:
              'linear-gradient(90deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.75) 32%, rgba(255,255,255,1) 100%)',
          }}
          initial={reduceMotion ? { scale: 1, opacity: 0.4 } : { scale: 0.02, opacity: 0 }}
          animate={
            reduceMotion
              ? { scale: 1, opacity: 0.4 }
              : { scale: [0.02, 1], opacity: [0, 1, 0] }
          }
          transition={
            reduceMotion
              ? { duration: 0 }
              : {
                  duration: CYCLE_SECONDS,
                  delay: beam.delay,
                  ease: 'easeIn',
                  repeat: Infinity,
                }
          }
        />
      ))}
    </div>
  );
}

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
