/** بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */
import { auth } from "@/lib/auth";
import { redirect } from "next/navigation";
import SignInButton from "@/components/auth/sign-in-button";

export const dynamic = "force-dynamic";

/**
 * The dedicated sign-in route. Signing in no longer lands the user in the
 * reconciliation application — it lands them on the subscription page.
 */
export default async function LoginPage() {
  const session = await auth();
  if (session) redirect("/subscription");

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 dark:bg-gray-950">
      <div className="w-full max-w-sm rounded-lg bg-white p-8 shadow-md text-center dark:bg-gray-900 dark:shadow-none dark:border dark:border-gray-800">
        <h1 className="mb-2 text-2xl font-bold text-gray-900 dark:text-gray-100">
          Bank Reconciliation System
        </h1>
        <p className="mb-6 text-sm text-gray-600 dark:text-gray-400">
          Sign in with Google to get started
        </p>
        <div className="flex justify-center">
          <SignInButton redirectTo="/subscription" />
        </div>
      </div>
    </div>
  );
}
/** وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
