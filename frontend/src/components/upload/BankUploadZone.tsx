/*
 * بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ
 * Bank Statement Upload Zone Component
 * Banking Reconciliation System Frontend
 */

'use client';

import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { FILE_VALIDATION, FILE_ICONS, FIELD_LABELS } from '../../lib/constants';
import { formatFileSize } from '../../lib/file-utils';
import type { BankStatementFile } from '../../types/upload';

interface BankUploadZoneProps {
  onFileUpload: (file: BankStatementFile) => void;
  uploadedFile: BankStatementFile | null;
  onFileRemove: () => void;
  dragOverZone: 'bank' | 'company' | null;
  onDragEnter: () => void;
  onDragLeave: () => void;
}

/**
 * Bank statement file upload zone component
 * Accepts only PDF files with drag-and-drop functionality
 */
export function BankUploadZone({
  onFileUpload,
  uploadedFile,
  onFileRemove,
  dragOverZone,
  onDragEnter,
  onDragLeave,
}: BankUploadZoneProps) {
  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        const file = acceptedFiles[0];

        // Create BankStatementFile object with validation
        const bankFile: BankStatementFile = {
          id: `bank-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
          file,
          name: file.name,
          size: file.size,
          type: file.type,
          uploadedAt: new Date(),
          isValid: FILE_VALIDATION.BANK_STATEMENT_TYPES.includes(file.type as any) &&
                   file.name.toLowerCase().endsWith('.pdf'),
          validationErrors: !FILE_VALIDATION.BANK_STATEMENT_TYPES.includes(file.type as any) ||
                           !file.name.toLowerCase().endsWith('.pdf')
                           ? [FILE_VALIDATION.ERROR_MESSAGES.INVALID_BANK_TYPE]
                           : undefined,
        };

        onFileUpload(bankFile);
      }
    },
    [onFileUpload]
  );

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
    },
    maxFiles: 1,
    multiple: false,
    onDragEnter: () => onDragEnter(),
    onDragLeave: () => onDragLeave(),
  });

  const isActive = isDragActive && !isDragReject;
  const isOver = dragOverZone === 'bank';

  return (
    <div
      {...getRootProps()}
      className={`
        relative border-2 border-dashed rounded-lg p-8 transition-all duration-200
        ${isActive || isOver
          ? 'border-[#FF8A65] bg-[#FFCDD2] scale-105'
          : 'border-[#FFCDD2] bg-white hover:border-[#FF8A65] hover:bg-[#FFEBEE]'}
        ${isDragReject ? 'border-red-500 bg-red-50' : ''}
        ${uploadedFile ? 'border-green-500 bg-green-50' : ''}
        cursor-pointer min-h-[200px] flex flex-col items-center justify-center
      `}
    >
      <input {...getInputProps()} />

      <div className="text-center space-y-4">
        {/* Icon */}
        <div className="text-6xl">
          {uploadedFile ? FILE_ICONS.PDF : FILE_ICONS.DEFAULT}
        </div>

        {/* Title */}
        <h3 className="text-lg font-semibold text-gray-800">
          {FIELD_LABELS.BANK_UPLOAD_TITLE}
        </h3>

        {/* Description */}
        <p className="text-sm text-gray-600">
          {FIELD_LABELS.BANK_UPLOAD_DESCRIPTION}
        </p>

        {/* Upload instructions */}
        {!uploadedFile && (
          <p className="text-sm text-gray-500">
            {FIELD_LABELS.BANK_UPLOAD_DROP_TEXT}
          </p>
        )}

        {/* Uploaded file info */}
        {uploadedFile && (
          <div className="space-y-2">
            <div className="flex items-center justify-center space-x-2">
              <span className="text-sm font-medium text-gray-800">
                {uploadedFile.name}
              </span>
              <span className="text-xs text-gray-500">
                ({formatFileSize(uploadedFile.size)})
              </span>
            </div>

            {/* Validation status */}
            {uploadedFile.isValid ? (
              <div className="flex items-center justify-center space-x-1 text-green-600 text-sm">
                <span>✓</span>
                <span>{FILE_VALIDATION.SUCCESS_MESSAGES.FILE_UPLOADED}</span>
              </div>
            ) : (
              <div className="text-red-600 text-sm">
                {uploadedFile.validationErrors?.join(', ')}
              </div>
            )}

            {/* Remove button */}
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onFileRemove();
              }}
              className="text-sm text-red-600 hover:text-red-700 underline"
            >
              Remove file
            </button>
          </div>
        )}

        {/* Drag active state */}
        {isActive && !uploadedFile && (
          <div className="text-sm font-medium text-[#FF8A65] animate-pulse">
            Drop PDF file here...
          </div>
        )}

        {/* Rejection state */}
        {isDragReject && (
          <div className="text-sm text-red-600">
            {FILE_VALIDATION.ERROR_MESSAGES.INVALID_BANK_TYPE}
          </div>
        )}
      </div>
    </div>
  );
}

/*
 * وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
 */