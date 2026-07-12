"use client";
/** بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */

import { SessionProvider } from "next-auth/react";

export default function AuthSessionProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  return <SessionProvider>{children}</SessionProvider>;
}
/** وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
