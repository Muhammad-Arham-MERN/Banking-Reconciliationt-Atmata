/* بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */
/* Skeleton UI component for loading states */

"use client";

export function Skeleton({ className }: { className?: string }) {
  return (
    <div
      className={`animate-pulse rounded-md bg-gray-200 ${className ?? ''}`}
    />
  );
}

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */