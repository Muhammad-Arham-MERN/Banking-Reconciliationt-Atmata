/* بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */

/**
 * CompanyBuilding — the simple multi-window facade the cinematic intro flies
 * toward. It is a static SVG; the intro applies the scale/fade motion around it.
 */

interface CompanyBuildingProps {
  className?: string;
}

export function CompanyBuilding({ className }: CompanyBuildingProps) {
  return (
    <svg
      className={className}
      viewBox="0 0 220 340"
      aria-hidden="true"
      focusable="false"
    >
      <defs>
        <linearGradient id="blBuildBody" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="#1f2937" />
          <stop offset="100%" stopColor="#0f172a" />
        </linearGradient>
        <linearGradient id="blBuildWin" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#fde68a" />
          <stop offset="100%" stopColor="#f59e0b" />
        </linearGradient>
      </defs>

      {/* body */}
      <rect x="20" y="20" width="180" height="320" rx="6" fill="url(#blBuildBody)" />
      <rect x="40" y="0" width="140" height="34" rx="4" fill="#111827" />

      {/* window grid */}
      {Array.from({ length: 9 }).map((_, row) =>
        Array.from({ length: 4 }).map((__, col) => (
          <rect
            key={`${row}-${col}`}
            x={40 + col * 38}
            y={50 + row * 30}
            width="24"
            height="18"
            rx="2"
            fill="url(#blBuildWin)"
            opacity={0.55 + ((row + col) % 3) * 0.15}
          />
        )),
      )}

      {/* entrance */}
      <rect x="90" y="300" width="40" height="40" rx="3" fill="#fbbf24" />
    </svg>
  );
}

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
