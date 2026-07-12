/** بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */
import { auth } from "@/lib/auth";
import { redirect } from "next/navigation";
import { UploadForm } from "../../components/upload/UploadForm";

export default async function UploadPage() {
  const session = await auth();
  if (!session) redirect("/");

  return (
    <main
      className="min-h-screen bg-gradient-to-br from-pink-50 to-red-50 py-8 px-4 sm:py-12 sm:px-6 lg:px-8"
      role="main"
      aria-label="Bank reconciliation file upload interface"
    >
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-6 sm:mb-8">
          {session.user?.name && (
            <div className="relative inline-block">
              <div className="absolute inset-0 bg-gradient-to-r from-emerald-200/40 via-teal-200/40 to-emerald-200/40 rounded-2xl blur-xl" />
              <div className="relative px-6 sm:px-8 py-4 sm:py-5 bg-white/70 backdrop-blur-sm rounded-2xl shadow-sm border border-emerald-100/60">
                <p className="text-2xl sm:text-3xl md:text-4xl font-bold bg-gradient-to-r from-emerald-700 via-teal-600 to-emerald-700 bg-clip-text text-transparent">
                  Assalamu Alaikum, {session.user.name}
                </p>
                <p className="text-sm text-emerald-600/70 mt-1 italic">
                  Peace be upon you
                </p>
              </div>
            </div>
          )}
        </div>
        <UploadForm />
        <div className="mt-8 sm:mt-12 bg-white rounded-lg shadow-md p-4 sm:p-6">
          <h2 className="text-lg sm:text-xl font-semibold text-gray-800 mb-4">
            How to use
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6 text-sm text-gray-600">
            <div>
              <h3 className="font-semibold text-gray-700 mb-2">1. Upload Bank Statement</h3>
              <p>Drag and drop your PDF bank statement file into the left upload zone</p>
            </div>
            <div>
              <h3 className="font-semibold text-gray-700 mb-2">2. Upload Company Data</h3>
              <p>Drag and drop your Excel company data file into the right upload zone</p>
            </div>
            <div className="sm:col-span-2 lg:col-span-1">
              <h3 className="font-semibold text-gray-700 mb-2">3. Configure & Submit</h3>
              <p>Configure your column mappings and submit for processing</p>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
/** وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
