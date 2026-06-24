/*
 * بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ
 * Main Upload Page
 * Banking Reconciliation System Frontend
 */

import { UploadForm } from '../../components/upload/UploadForm';

/**
 * Main upload interface page
 * Features two-column layout for bank statement and company data upload
 */
export default function UploadPage() {
  return (
    <main
      className="min-h-screen bg-gradient-to-br from-pink-50 to-red-50 py-8 px-4 sm:py-12 sm:px-6 lg:px-8"
      role="main"
      aria-label="Bank reconciliation file upload interface"
    >
      <div className="max-w-7xl mx-auto">
        {/* Page header */}
        <div className="text-center mb-6 sm:mb-8">
          <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold text-gray-900 mb-2">
            Bank Reconciliation System
          </h1>
          <p className="text-base sm:text-lg text-gray-600">
            Upload your files to automate reconciliation processing
          </p>
        </div>

        {/* Upload form with two-column layout */}
        <UploadForm />

        {/* Help section */}
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

/*
 * وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
 */