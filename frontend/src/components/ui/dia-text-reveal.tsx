/* بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */

"use client";

import { cn } from "@/lib/utils";

const DEFAULT_COLORS = ["#a855f7", "#d946ef", "#e879f9", "#818cf8"];

interface DiaTextRevealProps {
  /** Text to reveal with a sweeping gradient band. */
  text: string;
  /** Colors sampled across the moving gradient band. */
  colors?: string[];
  /** Sweep duration in seconds. */
  duration?: number;
  /** Delay before the sweep starts, in seconds. */
  delay?: number;
  /** Additional class names for the animated span. */
  className?: string;
}

/**
 * Dia text reveal: a horizontal neon band sweeps across the text, then the
 * text settles on the theme foreground color. Implemented as a pure CSS
 * animation (background-position sweep over a 200%-wide gradient clipped to
 * the text) so it renders reliably — the motion-value based original leaves
 * the text fully transparent if the animation doesn't apply.
 */
export function DiaTextReveal({
  text,
  colors = DEFAULT_COLORS,
  duration = 1.6,
  delay = 0,
  className,
}: DiaTextRevealProps) {
  const band = colors.join(", ");
  return (
    <span
      className={cn(
        "align-bottom leading-[100%] text-inherit dia-text-reveal",
        className
      )}
      style={{
        backgroundImage: `linear-gradient(90deg, var(--foreground) 0%, var(--foreground) 40%, ${band} 50%, var(--foreground) 60%, var(--foreground) 100%)`,
        backgroundSize: "200% 100%",
        WebkitBackgroundClip: "text",
        backgroundClip: "text",
        color: "transparent",
        animation: `dia-sweep ${duration}s ${delay}s ease-in-out forwards`,
      }}
    >
      {text}
    </span>
  );
}

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
