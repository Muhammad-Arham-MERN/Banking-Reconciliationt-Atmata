/* بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */

/**
 * GlareButton
 *
 * The subscription call-to-action: it lifts slightly on hover while a soft
 * glare sweeps across its face and passes out the other side.
 *
 * The label sits above the effect layer (no blend modes), so the text stays
 * legible while the glare passes over it.
 */
'use client';

import { cn } from '@/lib/utils';

export function GlareButton({ className, children, ...props }: React.ComponentProps<'button'>) {
  return (
    <button
      type="button"
      {...props}
      className={cn(
        'group relative w-full overflow-hidden rounded-xl px-6 py-3.5 text-base font-semibold text-white',
        'bg-gradient-to-r from-zinc-700 to-zinc-900',
        'shadow-lg shadow-black/20 transition-[transform,box-shadow] duration-200',
        'hover:-translate-y-0.5 hover:shadow-xl hover:shadow-black/30',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/70 focus-visible:ring-offset-2 focus-visible:ring-offset-transparent',
        'disabled:pointer-events-none disabled:opacity-60',
        className,
      )}
    >
      {/* The glare that sweeps in and passes out on hover. */}
      <span
        aria-hidden
        className="pointer-events-none absolute inset-y-0 left-[-45%] w-[45%] -skew-x-12 bg-gradient-to-r from-transparent via-white/70 to-transparent transition-[left] duration-700 ease-out group-hover:left-[125%]"
      />
      <span className="relative z-10">{children}</span>
    </button>
  );
}

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
