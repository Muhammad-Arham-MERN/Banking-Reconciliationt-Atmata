/* بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */

"use client";

import * as React from "react";
import { motion, AnimatePresence } from "motion/react";
import { StarsBackground } from "@/components/ui/stars-background";
import { ShootingStars } from "@/components/ui/shooting-stars";
import { UiverseServerLoader } from "@/components/ui/uiverse-server-loader";
import { AnimatedCircularProgressBar } from "@/components/ui/animated-circular-progress-bar";
import { Keyboard } from "@/components/ui/keyboard";
import { TypewriterEffectSmooth } from "@/components/ui/typewriter-effect";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import type {
  StageSentiment,
} from "@/lib/api/aiReconciliationClient";

/** Brand "AI neon" purple palette used across the loader overlays. */
const PRIMARY = "#a855f7";

export interface LiveEvent {
  /** Monotonic id so repeated stages (same key+message) stay unique in lists. */
  id: number;
  key: string;
  message: string;
  sentiment: StageSentiment;
  emoji: string;
}

interface LiveProcessingOverlayProps {
  /** Live stage frames appended as the SSE stream delivers them. */
  events: LiveEvent[];
  /** 0-100 circular-gauge value (parent computes from sentiments). */
  progress: number;
  /** When true, hide the gauge/events/cauldron and show the completion choreography. */
  done: boolean;
  /** Called when the user confirms Stop from the bottom-left dialog. */
  onStop: () => void;
  /** Called once the keyboard has finished auto-typing "Processing Complete". */
  onTypingComplete?: () => void;
}

const PROGRESS_WORDS = [
  { text: "Processing" },
  { text: "Complete" },
];

const COMPLETE_PHRASE = "Processing Complete";

// Map each character of the completion phrase to a physical KeyboardEvent.code
// so the aceternity Keyboard lights up the real keys as it "types".
const CHAR_TO_CODE: Record<string, string> = {
  P: "KeyP", r: "KeyR", o: "KeyO", c: "KeyC", e: "KeyE", s: "KeyS",
  i: "KeyI", n: "KeyN", g: "KeyG", m: "KeyM", l: "KeyL", t: "KeyT",
  a: "KeyA", " ": "Space",
};

/**
 * Live, SSE-driven processing overlay for /reconcile-ai.
 *
 * Layout (no dialog - it is the page's full-screen state):
 *  - The 3D isometric "cauldron" loader sits in the CENTER of the animated
 *    circular progress gauge (the gauge "cooks" while the cauldron heats).
 *  - The current + recent live events stream in below, in a multi-step style
 *    list (not a modal), with sentiment-colored icons.
 *  - The Stop control lives at the BOTTOM-LEFT and asks for confirmation.
 *  - When `done` flips, the processing cluster fades out and the keyboard
 *    types "Processing Complete" (purple glow per key) in sync with the
 *    typewriter; then the parent fades the whole overlay out to reveal the
 *    reconciliation results.
 */
export function LiveProcessingOverlay({
  events,
  progress,
  done,
  onStop,
  onTypingComplete,
}: LiveProcessingOverlayProps) {
  const [mounted, setMounted] = React.useState(false);
  const [showProcessing, setShowProcessing] = React.useState(true);
  const [confirmOpen, setConfirmOpen] = React.useState(false);
  const [typingDone, setTypingDone] = React.useState(false);
  const typingDoneRef = React.useRef(false);
  const onTypingCompleteRef = React.useRef(onTypingComplete);
  onTypingCompleteRef.current = onTypingComplete;

  // Fade the whole overlay IN on mount (not an instant pop).
  React.useEffect(() => {
    const raf = requestAnimationFrame(() => setMounted(true));
    return () => cancelAnimationFrame(raf);
  }, []);

  // Lock body scroll while the overlay is mounted.
  React.useEffect(() => {
    const originalOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = originalOverflow;
    };
  }, []);

  // Completion choreography: when done arrives, fade out the processing
  // cluster and auto-"type" "Processing Complete" on the keyboard. Real
  // KeyboardEvents are dispatched so the aceternity Keyboard's document
  // listener lights the actual keys in sequence (the component only reacts to
  // physical/synthetic key events — it has no built-in auto-typer). Each key
  // press is short so the typewriter text and the key glow stay in step; when
  // the last key is released we tell the parent the reveal may begin.
  React.useEffect(() => {
    if (!done) {
      setTypingDone(false);
      return;
    }
    typingDoneRef.current = false;
    // Fade the gauge + cauldron + event feed out first.
    const t1 = setTimeout(() => setShowProcessing(false), 60);
    // Then start auto-typing once the keyboard is on screen.
    const timers: ReturnType<typeof setTimeout>[] = [];
    const t2 = setTimeout(() => {
      const chars = COMPLETE_PHRASE.split("");
      const pressMs = 90; // time each key stays visually pressed
      const gapMs = 70; // pause between key releases
      chars.forEach((ch, i) => {
        const code = CHAR_TO_CODE[ch];
        const at = i * (pressMs + gapMs);
        if (code) {
          timers.push(
            setTimeout(() => {
              document.dispatchEvent(
                new KeyboardEvent("keydown", { code, key: ch, bubbles: true })
              );
            }, at)
          );
          timers.push(
            setTimeout(() => {
              document.dispatchEvent(
                new KeyboardEvent("keyup", { code, key: ch, bubbles: true })
              );
            }, at + pressMs)
          );
        }
      });
      const total = chars.length * (pressMs + gapMs) + 400;
      timers.push(
        setTimeout(() => {
          typingDoneRef.current = true;
          setTypingDone(true);
          onTypingCompleteRef.current?.();
        }, total)
      );
    }, 900);
    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
      timers.forEach(clearTimeout);
    };
  }, [done]);

  const current = events.length > 0 ? events[events.length - 1] : null;
  // Keep a short trailing window of the most recent events for the feed.
  const recent = events.slice(-4);

  return (
    <div
      className={cn(
        "fixed inset-0 z-50 flex items-center justify-center overflow-hidden bg-background transition-opacity duration-700",
        mounted ? "opacity-100" : "opacity-0"
      )}
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

      {/* ============ Processing cluster (gauge + cauldron + events) ============ */}
      <AnimatePresence>
        {showProcessing && (
          <motion.div
            key="processing"
            initial={{ opacity: 1 }}
            exit={{ opacity: 0, transition: { duration: 0.7 } }}
            className="relative flex w-full max-w-3xl flex-col items-center gap-10 px-6"
          >
            {/* Circular gauge with the cauldron centered inside it */}
            <div className="relative flex items-center justify-center">
              <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
                <AnimatedCircularProgressBar
                  value={progress}
                  gaugePrimaryColor={PRIMARY}
                  gaugeSecondaryColor="rgba(0,0,0,0.08)"
                  className="size-72 text-3xl"
                />
              </div>
              {/* Percentage readout sits at the gauge's center behind the loader? 
                  No - the cauldron occupies the center; show % under it instead. */}
              <UiverseServerLoader className="scale-[0.9]" />
              <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 rounded-full bg-purple-500/10 px-3 py-0.5 text-sm font-semibold text-purple-600 dark:text-purple-300">
                {Math.round(progress)}%
              </div>
            </div>

            {/* Current event + recent event feed (multi-step style, NOT a dialog) */}
            <div className="flex min-h-[6.5rem] w-full max-w-xl flex-col items-center justify-center gap-2">
              {current ? (
                <div className="flex items-center gap-3 text-center">
                  <span className="text-2xl" aria-hidden>
                    {current.emoji}
                  </span>
                  <span className="bg-gradient-to-r from-purple-600 via-fuchsia-500 to-purple-600 bg-clip-text text-lg font-semibold text-transparent sm:text-xl">
                    {current.message}
                  </span>
                </div>
              ) : (
                <div className="text-lg font-medium text-muted-foreground">
                  Starting up…
                </div>
              )}

              {/* trailing feed */}
              {recent.length > 1 && (
                <div className="mt-1 flex flex-col items-center gap-1">
                  {recent.slice(0, -1).map((ev) => (
                    <div
                      key={ev.id}
                      className="flex items-center gap-2 text-xs text-muted-foreground/70"
                    >
                      <span aria-hidden>{ev.emoji}</span>
                      <span className="line-clamp-1 max-w-sm truncate">
                        {ev.message}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ============ Completion choreography (keyboard + typewriter) ============ */}
      <AnimatePresence>
        {done && !showProcessing && (
          <motion.div
            key="completion"
            initial={{ opacity: 0, scale: 0.97 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6 }}
            className="relative flex flex-col items-center gap-8 px-6"
          >
            <TypewriterEffectSmooth
              words={PROGRESS_WORDS.map((w) => ({
                text: w.text,
                className:
                  "bg-gradient-to-r from-purple-600 via-fuchsia-500 to-purple-600 bg-clip-text text-transparent",
              }))}
              cursorClassName="bg-purple-500"
              className="text-3xl sm:text-5xl"
            />
            <div className="drop-shadow-[0_0_18px_rgba(168,85,247,0.55)] transition-shadow duration-300">
              <Keyboard enableSound={false} />
            </div>
            <div className="text-sm font-medium text-muted-foreground">
              {typingDone ? "Finalizing your results…" : "Processing Complete"}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ============ Stop (bottom-left, confirm first) ============ */}
      {!done && (
        <div className="absolute bottom-6 left-6 z-10">
          <Button
            type="button"
            variant="outline"
            onClick={() => setConfirmOpen(true)}
            className="gap-2 rounded-full border-red-300/60 text-red-600 hover:bg-red-50 hover:text-red-700 dark:border-red-500/40 dark:text-red-300 dark:hover:bg-red-950/50"
          >
            <span className="inline-block h-2 w-2 rounded-full bg-red-500 animate-pulse" />
            Stop Processing
          </Button>

          <Dialog open={confirmOpen} onOpenChange={setConfirmOpen}>
            <DialogContent showCloseButton={false} className="max-w-sm">
              <DialogHeader>
                <DialogTitle>Stop processing?</DialogTitle>
                <DialogDescription>
                  This will cancel the AI run and discard the current analysis.
                  You can start a new reconciliation afterwards.
                </DialogDescription>
              </DialogHeader>
              <DialogFooter>
                <Button
                  variant="outline"
                  onClick={() => setConfirmOpen(false)}
                >
                  Keep going
                </Button>
                <Button
                  variant="destructive"
                  onClick={() => {
                    setConfirmOpen(false);
                    onStop();
                  }}
                >
                  Stop processing
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      )}
    </div>
  );
}

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
