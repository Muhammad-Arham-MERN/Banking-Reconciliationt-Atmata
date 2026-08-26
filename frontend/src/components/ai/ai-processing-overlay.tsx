/* بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */

"use client";

import * as React from "react";
import { DiaTextReveal } from "@/components/ui/dia-text-reveal";
import { StarsBackground } from "@/components/ui/stars-background";
import { ShootingStars } from "@/components/ui/shooting-stars";
import { UiverseServerLoader } from "@/components/ui/uiverse-server-loader";

const MESSAGES = [
  "Gotcha",
  "We are processing your File with AI",
  "This may take some time",
] as const;

const NEON_COLORS = ["#a855f7", "#d946ef", "#e879f9", "#818cf8"];

// Slower cadence so each sweep reads smoothly (sweep ~2.4s + pause).
const STEP_MS = 3600;
const LOADER_DELAY_MS = STEP_MS * (MESSAGES.length - 1) + 2200;

interface AIProcessingOverlayProps {
  /** Called when the user clicks Stop; should cancel the backend run. */
  onStop?: () => void;
}

/**
 * Full-screen AI processing overlay (FR-016 enhancement).
 * Sequence: three DiaTextReveal messages play one by one ("Gotcha" →
 * "We are processing your File with AI" → "This may take some time"),
 * then the 3D isometric loader fades in over a starry/shooting-stars
 * background that matches the light/dark theme.
 */
export function AIProcessingOverlay({ onStop }: AIProcessingOverlayProps) {
  const [messageIndex, setMessageIndex] = React.useState(0);
  const [showLoader, setShowLoader] = React.useState(false);

  // DiaTextReveal's sweep is a CSS animation; drive the sequence on a fixed
  // schedule: one message per STEP_MS, then reveal the loader afterwards.
  React.useEffect(() => {
    const timers: ReturnType<typeof setTimeout>[] = [];

    MESSAGES.forEach((_, i) => {
      if (i === 0) return;
      timers.push(setTimeout(() => setMessageIndex(i), STEP_MS * i));
    });
    timers.push(setTimeout(() => setShowLoader(true), LOADER_DELAY_MS));

    return () => timers.forEach(clearTimeout);
  }, []);

  // Lock body scroll while the full-screen overlay is mounted, so the page
  // behind doesn't show a scrollbar next to the loader.
  React.useEffect(() => {
    const originalOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = originalOverflow;
    };
  }, []);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center overflow-hidden bg-background"
      role="status"
      aria-live="polite"
      aria-label="AI processing in progress"
    >
      {/* Starry background */}
      <div className="pointer-events-none absolute inset-0">
        <StarsBackground
          starDensity={0.0003}
          allStarsTwinkle
          className="opacity-90 dark:opacity-100"
        />
        <ShootingStars
          starColor="#a855f7"
          trailColor="#818cf8"
          className="opacity-70 dark:opacity-100"
        />
      </div>

      <div className="relative flex flex-col items-center gap-10 px-6">
        {/* Message area: one DiaTextReveal at a time */}
        <div className="h-16 sm:h-20 flex items-center justify-center">
          {MESSAGES.map((msg, i) => (
            <div
              key={msg}
              className={i === messageIndex ? "block" : "hidden"}
            >
              <DiaTextReveal
                text={msg}
                colors={NEON_COLORS}
                duration={2.4}
                delay={0.3}
                className="text-2xl sm:text-3xl md:text-4xl font-bold tracking-tight"
              />
            </div>
          ))}
        </div>

        {/* Loader fades in after the messages */}
        <div
          className={`transition-opacity duration-700 ${
            showLoader ? "opacity-100" : "opacity-0 pointer-events-none"
          }`}
        >
          <UiverseServerLoader className="scale-125" />
        </div>

        {/* Stop button */}
        {onStop && (
          <button
            type="button"
            onClick={onStop}
            className="mt-2 inline-flex items-center gap-2 rounded-full border border-red-300/60 bg-red-50/60 px-6 py-2 text-sm font-medium text-red-600 transition-colors hover:bg-red-100/80 dark:border-red-500/40 dark:bg-red-950/40 dark:text-red-300 dark:hover:bg-red-900/50"
          >
            <span className="inline-block h-2.5 w-2.5 rounded-full bg-red-500 animate-pulse" />
            Stop Processing
          </button>
        )}
      </div>
    </div>
  );
}

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
