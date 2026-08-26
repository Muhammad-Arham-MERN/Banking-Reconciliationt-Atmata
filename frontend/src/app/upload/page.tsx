/** بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */
import { auth } from "@/lib/auth";
import { redirect } from "next/navigation";

export const dynamic = "force-dynamic";
import { UploadForm } from "../../components/upload/UploadForm";

export default async function UploadPage() {
  const session = await auth();
  if (!session) redirect("/");

  return (
    <main
      className="min-h-screen bg-gradient-to-br from-pink-50 to-red-50 dark:from-gray-950 dark:to-gray-900 py-8 px-4 sm:py-12 sm:px-6 lg:px-8"
      role="main"
      aria-label="Bank reconciliation file upload interface"
    >
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-6 sm:mb-8">
          {session.user?.name && (
            <div className="relative inline-block">
              {/* Soft neon glow behind the block (like a shining drop shadow) */}
              <div className="absolute -inset-3 bg-gradient-to-r from-purple-400/50 via-fuchsia-300/50 to-purple-400/50 rounded-3xl blur-2xl" />
              <div className="relative px-8 sm:px-10 py-5 sm:py-6 rounded-3xl bg-white/80 backdrop-blur-sm border border-purple-200/60 shadow-lg dark:bg-gray-900/80 dark:border-purple-500/30">
                <p className="text-2xl sm:text-3xl md:text-4xl font-extrabold bg-gradient-to-r from-purple-600 via-fuchsia-500 to-purple-600 dark:from-purple-300 dark:via-fuchsia-300 dark:to-purple-300 bg-clip-text text-transparent drop-shadow-[0_0_6px_rgba(147,51,234,0.25)] dark:drop-shadow-[0_0_6px_rgba(192,132,252,0.35)]">
                  Assalamu Alaikum, {session.user.name}
                </p>
                <p className="text-sm italic bg-gradient-to-r from-purple-600 via-fuchsia-500 to-purple-600 dark:from-purple-300 dark:via-fuchsia-300 dark:to-purple-300 bg-clip-text text-transparent drop-shadow-[0_0_4px_rgba(147,51,234,0.2)] dark:drop-shadow-[0_0_4px_rgba(192,132,252,0.25)] mt-1">
                  Peace be upon you
                </p>
              </div>
            </div>
          )}
        </div>
        <UploadForm />
        <div className="mt-8 sm:mt-12 bg-white rounded-lg shadow-md p-4 sm:p-6 dark:bg-gray-900 dark:shadow-none dark:border dark:border-gray-800">
          <h2 className="text-lg sm:text-xl font-semibold text-gray-800 mb-4 dark:text-gray-100">
            How to use
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6 text-sm text-gray-600 dark:text-gray-400">
            <div>
              <h3 className="font-semibold text-gray-700 mb-2 dark:text-gray-200">1. Upload Bank Statement</h3>
              <p>Drag and drop your PDF bank statement file into the left upload zone</p>
            </div>
            <div>
              <h3 className="font-semibold text-gray-700 mb-2 dark:text-gray-200">2. Upload Company Data</h3>
              <p>Drag and drop your Excel company data file into the right upload zone</p>
            </div>
            <div className="sm:col-span-2 lg:col-span-1">
              <h3 className="font-semibold text-gray-700 mb-2 dark:text-gray-200">3. Configure & Submit</h3>
              <p>Configure your column mappings and submit for processing</p>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
/** وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
