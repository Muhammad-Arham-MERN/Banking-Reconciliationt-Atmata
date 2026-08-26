/* بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */

"use client";
import { useSession, signOut } from "next-auth/react";
import { Skeleton } from "@/components/ui/skeleton";

export default function SessionStatus() {
  const { data: session, status } = useSession();

  // Skeleton while session is loading
  if (status === "loading") {
    return (
      <div className="flex items-center gap-4">
        <Skeleton className="h-8 w-8 rounded-full" />
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-8 w-20 rounded-md" />
      </div>
    );
  }

  // No session — shouldn't happen on protected pages, but handle gracefully
  if (!session) return null;

  return (
    <div className="flex items-center gap-4">
      {session.user?.image && (
        <img
          src={session.user.image}
          alt=""
          className="h-8 w-8 rounded-full"
        />
      )}
      <span className="text-sm text-gray-700 dark:text-gray-300">
        {session.user?.name || session.user?.email}
      </span>
      <button
        onClick={() => signOut({ redirectTo: "/" })}
        className="rounded-md bg-gray-100 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
      >
        Sign out
      </button>
    </div>
  );
}
/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */