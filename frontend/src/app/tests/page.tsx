/** بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */
import { auth } from "@/lib/auth";
import { redirect } from "next/navigation";

export const dynamic = "force-dynamic";
import { DummyResultsViewer } from "./DummyResultsViewer";

export default async function TestsPage() {
  const session = await auth();
  if (!session) redirect("/");

  return (
    <main
      className="min-h-screen bg-gradient-to-br from-pink-50 to-red-50 dark:from-gray-950 dark:to-gray-900 py-8 px-4 sm:py-12 sm:px-6 lg:px-8"
      role="main"
      aria-label="Dummy reconciliation test data"
    >
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-6 sm:mb-8">
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-800 dark:text-gray-100">
            Test Reconciliation Data
          </h1>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            600 transactions, 150+ discrepancies across all four categories —
            with broken-cheque and reversal patterns embedded for the Reconciler
            Agent. Click &quot;Reconcile With Agent&quot; to test the advisor.
          </p>
        </div>
        <DummyResultsViewer />
      </div>
    </main>
  );
}
/** وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
