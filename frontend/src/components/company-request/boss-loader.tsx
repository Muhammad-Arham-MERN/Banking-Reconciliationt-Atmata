/* بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */

/**
 * BossLoader — the bored-boss character, ported from the standalone
 * frontend/boss-loader.html reference (removed after this port). The SVG art and
 * all motion live in boss-loader.module.css; this file only renders the markup
 * and exposes three modes the onboarding flow drives:
 *
 *  - `idle`    the boss waits, tapping his pen (shown while the visitor types)
 *  - `handsUp` the boss raises the pen (played on each "Next")
 *  - `smile`   the boss smiles (played after the final answer)
 */
'use client';

import { cn } from '@/lib/utils';
import styles from './boss-loader.module.css';

export type BossMode = 'straight' | 'idle' | 'handsUp' | 'smile';

interface BossLoaderProps {
  mode?: BossMode;
  className?: string;
}

export function BossLoader({ mode = 'idle', className }: BossLoaderProps) {
  const modeClass =
    mode === 'straight'
      ? styles.modeStraight
      : mode === 'handsUp'
        ? styles.modeHandsUp
        : mode === 'smile'
          ? styles.modeSmile
          : styles.modeIdle;

  return (
    <svg
      className={cn(styles.bossLoader, modeClass, className)}
      viewBox="0 0 700 600"
      role="img"
      aria-label="Your onboarding guide, waiting"
    >
      <defs>
        <linearGradient id="blCrease" x1="0" y1="0" x2="0" y2="1">
          <stop className={styles.blCrease1} offset="0%" />
          <stop className={styles.blCrease2} offset="100%" />
        </linearGradient>
        <filter id="blTableShadow" x="-25%" y="-40%" width="150%" height="200%">
          <feDropShadow dx="0" dy="9" stdDeviation="11" floodColor="#0b1020" floodOpacity="0.2" />
        </filter>
      </defs>

      <g className={styles.boss}>
        {/* chair */}
        <g>
          <path className={styles.blTable2} d="M222 466 L239 466 L236 582 L225 582 Z" />
          <path className={styles.blTable2} d="M361 466 L378 466 L375 582 L364 582 Z" />
          <rect className={styles.blTable2} x="214" y="448" width="172" height="24" rx="9" />
          <rect className={styles.blTable} x="214" y="448" width="172" height="15" rx="8" />
        </g>

        {/* neck */}
        <path className={styles.blSkin2} d="M283 236 L283 302 Q300 314 317 302 L317 236 Z" />

        {/* torso */}
        <path className={styles.blSuit} d="M300 288 C348 288 378 290 382 306 L372 450 L228 450 L218 306 C222 290 252 288 300 288 Z" />
        <path className={styles.blWhite} d="M283 288 L300 324 L317 288 L308 285 L300 309 L292 285 Z" />
        <path className={styles.blAccent2} d="M295 305 L305 305 L307 316 L300 321 L293 316 Z" />
        <path className={styles.blAccent} d="M296 319 L304 319 L309 344 L300 388 L291 344 Z" />

        {/* seated crease */}
        <path className={styles.blCrease} d="M249 416 L293 416 L290 452 L252 452 Z" />
        <path className={styles.blCrease} d="M307 416 L351 416 L348 452 L310 452 Z" />

        {/* legs + shoes */}
        <path className={styles.blSuit2} d="M254 394 L288 394 L284 546 L258 546 Z" />
        <path className={styles.blSuit2} d="M312 394 L346 394 L342 546 L316 546 Z" />
        <rect className={styles.blShoe} x="246" y="540" width="52" height="38" rx="17" />
        <rect className={styles.blShoe} x="302" y="540" width="52" height="38" rx="17" />

        {/* head + face — grouped so the intro can sit him upright (un-tilt) */}
        <g className={styles.headGroup}>
        {/* ears + head */}
        <ellipse className={styles.blSkin2} cx="241" cy="206" rx="10" ry="14" transform="rotate(-8 300 270)" />
        <ellipse className={styles.blSkin2} cx="359" cy="206" rx="10" ry="14" transform="rotate(-8 300 270)" />
        <ellipse className={styles.blSkin} cx="300" cy="196" rx="60" ry="68" transform="rotate(-8 300 270)" />
        <path
          className={styles.blHair}
          transform="rotate(-8 300 270)"
          d="M244 194 C244 148 268 126 300 126 C332 126 356 148 356 194 C348 172 342 164 332 162 C316 156 300 158 288 164 C272 171 256 178 244 194 Z"
        />

        {/* face */}
        <path className={styles.blNose} transform="rotate(-8 300 270)" d="M300 208 L296 224 Q300 228 304 224" />
        <path className={styles.blMouth} transform="rotate(-8 300 270)" d="M287 241 L313 241" />
        <path className={styles.blSmile} transform="rotate(-8 300 270)" d="M283 237 Q300 252 317 237" />

        <path className={styles.brow} d="M262 179 Q276 174 289 179" />
        <path className={styles.brow} d="M311 179 Q324 174 338 179" />

        <g className={cn(styles.eye, styles.eyeL)}>
          <ellipse className={styles.blEye} cx="276" cy="196" rx="13" ry="10.5" />
          <g className={styles.pupil}>
            <circle className={styles.blInk} cx="276" cy="199" r="6" />
          </g>
          <path className={styles.blLid} d="M263 185 H289 V195 Q276 202.5 263 195 Z" />
          <path className={styles.blLash} d="M263 194.5 Q276 202 289 194.5" />
        </g>
        <g className={cn(styles.eye, styles.eyeR)}>
          <ellipse className={styles.blEye} cx="324" cy="196" rx="13" ry="10.5" />
          <g className={styles.pupil}>
            <circle className={styles.blInk} cx="324" cy="199" r="6" />
          </g>
          <path className={styles.blLid} d="M311 185 H337 V195 Q324 202.5 311 195 Z" />
          <path className={styles.blLash} d="M311 194.5 Q324 202 337 194.5" />
        </g>
        </g>

        {/* right arm: elbow on the desk, cheek on the fist. Lowered onto the
            desk for the intro's "straight" pose, then raised and held. */}
        <g className={styles.blCheekArm}>
          <path className={styles.blStrokeSuit} d="M250 308 L202 370 L262 280" strokeWidth="38" />
          <path className={styles.blSkin} d="M252 282 C244 264 258 248 276 250 C293 252 298 268 290 280 C282 292 262 294 252 282 Z" />
        </g>

        {/* left arm (animated) */}
        <path className={cn(styles.armUpper, styles.blStrokeSuit)} d="M352 306 L426 368" strokeWidth="38" />
        <path className={cn(styles.armFore, styles.blStrokeSuit2)} d="M426 368 L452 342" strokeWidth="34" />

        {/* desk */}
        <g filter="url(#blTableShadow)">
          <path className={styles.blTable2} d="M138 400 L184 400 L178 582 L146 582 Z" />
          <path className={styles.blTable2} d="M504 400 L550 400 L544 582 L512 582 Z" />
          <rect className={styles.blTable2} x="82" y="384" width="524" height="36" rx="10" />
          <rect className={styles.blTable} x="82" y="384" width="524" height="22" rx="9" />
        </g>

        {/* left hand + pen (animated) */}
        <g className={styles.armHand}>
          <path className={styles.blSkin} d="M450 334 C466 326 481 336 479 351 C477 366 460 374 450 365 C441 357 441 342 450 334 Z" />
          <rect className={styles.blAccent} x="466" y="336" width="7" height="42" rx="3.5" />
          <path className={styles.blInk} d="M466 376 L469.5 385 L473 376 Z" />
        </g>

        {/* tap ripples */}
        <g>
          <ellipse className={cn(styles.ripple, styles.r1)} cx="469.5" cy="384" rx="13" ry="4.2" />
          <ellipse className={cn(styles.ripple, styles.r2)} cx="469.5" cy="384" rx="13" ry="4.2" />
          <ellipse className={cn(styles.ripple, styles.r3)} cx="469.5" cy="384" rx="13" ry="4.2" />
          <ellipse className={cn(styles.ripple, styles.r4)} cx="469.5" cy="384" rx="13" ry="4.2" />
        </g>
      </g>
    </svg>
  );
}

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
