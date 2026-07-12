/** بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */
import { auth } from "@/lib/auth";
import { redirect } from "next/navigation";
import SignInButton from "@/components/auth/sign-in-button";

export default async function Home() {
  const session = await auth();
  if (session) redirect("/upload");

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="w-full max-w-sm rounded-lg bg-white p-8 shadow-md text-center">
        <h1 className="mb-2 text-2xl font-bold text-gray-900">
          Bank Reconciliation System
        </h1>
        <p className="mb-6 text-sm text-gray-600">
          Sign in with Google to get started
        </p>
        <div className="flex justify-center">
          <SignInButton redirectTo="/upload" />
        </div>
      </div>
    </div>
  );
}
/** وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
