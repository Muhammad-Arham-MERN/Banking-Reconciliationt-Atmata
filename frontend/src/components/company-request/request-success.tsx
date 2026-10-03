/* بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */

/**
 * RequestSuccess — the closing message, written with the existing Aceternity
 * typewriter (text-generate) effect. The copy is reproduced verbatim from
 * FR-011; the flow owns the 5-second auto-close (FR-012).
 */
'use client';

import { TypewriterEffect } from '@/components/ui/typewriter-effect';

const SUCCESS_MESSAGE =
  'Request Sent Successfully - Please Wait For The Team To Contact Your Representative';

export function RequestSuccess() {
  const words = SUCCESS_MESSAGE.split(' ').map((text) => ({ text }));

  return (
    <div className="mx-auto w-full max-w-3xl px-8 text-center">
      <TypewriterEffect
        words={words}
        className="text-white"
        cursorClassName="bg-white"
      />
    </div>
  );
}

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
