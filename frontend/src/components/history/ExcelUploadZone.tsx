/* بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */

/**
 * ExcelUploadZone
 *
 * A react-dropzone field for uploading a filled past-reconciliation Excel
 * template. Mirrors CompanyUploadZone's validation (.xlsx/.xls, single file)
 * and shows the chosen file with a remove action.
 */
'use client';

import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { FileSpreadsheet, UploadCloud, X } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ExcelUploadZoneProps {
  /** Called with the chosen Excel file (already validated). */
  onFileSelected: (file: File) => void;
  /** Currently chosen file, if any. */
  selectedFile: File | null;
  onFileRemove: () => void;
}

export function ExcelUploadZone({
  onFileSelected,
  selectedFile,
  onFileRemove,
}: ExcelUploadZoneProps) {
  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) onFileSelected(acceptedFiles[0]);
    },
    [onFileSelected]
  );

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
    },
    maxFiles: 1,
    multiple: false,
  });

  return (
    <div
      {...getRootProps()}
      className={cn(
        'relative flex min-h-[160px] cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-6 text-center transition-all duration-200',
        isDragActive && !isDragReject
          ? 'border-emerald-500 bg-emerald-50 scale-[1.01] dark:bg-emerald-950/40'
          : 'border-emerald-200 bg-white hover:border-emerald-400 hover:bg-emerald-50/40 dark:border-emerald-900 dark:bg-gray-900 dark:hover:bg-emerald-950/20',
        isDragReject && 'border-red-500 bg-red-50 dark:bg-red-950/30'
      )}
    >
      <input {...getInputProps()} />

      {selectedFile ? (
        <div className="flex items-center gap-3">
          <FileSpreadsheet className="size-8 text-emerald-600 dark:text-emerald-400" />
          <div className="text-left">
            <p className="text-sm font-medium text-foreground">{selectedFile.name}</p>
            <p className="text-xs text-muted-foreground">
              {(selectedFile.size / 1024).toFixed(1)} KB — ready to import
            </p>
          </div>
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onFileRemove();
            }}
            title="Remove file"
            className="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
          >
            <X className="size-4" />
          </button>
        </div>
      ) : (
        <div className="space-y-2">
          <UploadCloud className="mx-auto size-8 text-emerald-600 dark:text-emerald-400" />
          <p className="text-sm font-medium text-foreground">
            Drop your filled Excel file here, or click to browse
          </p>
          <p className="text-xs text-muted-foreground">Accepts .xlsx / .xls (max 10 MB)</p>
          {isDragReject && (
            <p className="text-xs text-destructive">Only .xlsx / .xls files are accepted</p>
          )}
        </div>
      )}
    </div>
  );
}

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
