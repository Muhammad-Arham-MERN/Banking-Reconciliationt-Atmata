# Quickstart Guide: Frontend File Upload Interface

**Feature**: 001-file-upload-ui  
**Date**: 2025-01-17  
**Developer**: Muhammad Armar

## Overview

This guide provides step-by-step instructions for implementing the frontend file upload interface using Next.js and ShadCN UI. Follow these steps in order to build the feature according to the specification.

## Prerequisites

**Required Software**:
- Node.js 18+ installed
- npm or yarn package manager
- Git for version control

**Required Knowledge**:
- Basic React and TypeScript
- Familiarity with Next.js App Router
- Understanding of Tailwind CSS

## Project Setup

### Step 1: Initialize Next.js Project

```bash
# Create new Next.js project (if not exists)
npx create-next-app@latest bank-reconciliation-frontend --typescript --tailwind --app
cd bank-reconciliation-frontend
```

### Step 2: Install Dependencies

```bash
# Install ShadCN UI (if not installed)
npx shadcn-ui@latest init

# Install required ShadCN components
npx shadcn-ui@latest add input
npx shadcn-ui@latest add select
npx shadcn-ui@latest add button
npx shadcn-ui@latest add label

# Install additional dependencies
npm install react-dropzone
```

### Step 3: Configure Project Structure

```bash
# Create directory structure
mkdir -p src/components/upload
mkdir -p src/lib
mkdir -p src/types
```

## Implementation Steps

### Step 4: Set Up Theme and Constants

Create `src/lib/constants.ts`:

```typescript
بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ

// Theme colors for peach-red design
export const THEME_COLORS = {
  background: '#FFE5E5',      // Light peach-red background
  uploadZone: '#FF6B6B',     // Dark peach-red for upload zones
  uploadZoneHover: '#EE5A5A', // Darker shade for hover state
  text: '#2D2D2D',           // Dark text for readability
  error: '#DC2626',          // Red for errors
  success: '#16A34A',        // Green for success states
} as const;

// File validation constants
export const FILE_VALIDATION = {
  bank: {
    allowedExtensions: ['.pdf'],
    allowedMimeTypes: ['application/pdf'],
    maxSizeBytes: 50 * 1024 * 1024, // 50MB
    errorMessage: 'Only PDF files are accepted for bank statements'
  },
  company: {
    allowedExtensions: ['.xlsx'],
    allowedMimeTypes: ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
    maxSizeBytes: 50 * 1024 * 1024, // 50MB
    errorMessage: 'Only XLSX files are accepted for company data'
  }
} as const;

// Format options
export const FORMAT_OPTIONS = [
  'debit + credit format',
  'debit | credit format'
] as const;

export type FormatOption = typeof FORMAT_OPTIONS[number];

وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
```

### Step 5: Create TypeScript Types

Create `src/types/upload.ts`:

```typescript
بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ

export interface UploadedFile {
  id: string;
  file: File;
  name: string;
  size: number;
  type: string;
  uploadedAt: Date;
  isValid: boolean;
  validationErrors?: string[];
}

export type FormatType = 'debit-plus-credit' | 'debit-pipe-credit';

export interface ColumnMappingConfiguration {
  formatType: FormatType;
  debitPlusCreditFields?: {
    transactionDateColumn: string;
    debitPlusCreditColumn: string;
    transactionDetailsColumn: string;
  };
  debitPipeCreditFields?: {
    transactionDateColumn: string;
    debitColumn: string;
    creditColumn: string;
    transactionDetailsColumn: string;
  };
  isComplete: boolean;
  validationErrors?: Record<string, string>;
}

export interface SubmissionPackage {
  id: string;
  bankStatement: UploadedFile;
  companyData: UploadedFile;
  columnMapping: ColumnMappingConfiguration;
  submittedAt: Date;
  status: 'pending' | 'uploading' | 'success' | 'error';
  errorMessage?: string;
}

وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
```

### Step 6: Create File Validation Utilities

Create `src/lib/file-utils.ts`:

```typescript
بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ

import { FILE_VALIDATION } from './constants';
import type { UploadedFile } from '@/types/upload';

export function validateBankFile(file: File): UploadedFile {
  const validationErrors: string[] = [];
  
  // Check file extension
  const hasValidExtension = FILE_VALIDATION.bank.allowedExtensions.some(ext => 
    file.name.toLowerCase().endsWith(ext)
  );
  if (!hasValidExtension) {
    validationErrors.push(FILE_VALIDATION.bank.errorMessage);
  }
  
  // Check MIME type
  if (!FILE_VALIDATION.bank.allowedMimeTypes.includes(file.type)) {
    validationErrors.push(FILE_VALIDATION.bank.errorMessage);
  }
  
  // Check file size
  if (file.size > FILE_VALIDATION.bank.maxSizeBytes) {
    validationErrors.push('File size exceeds 50MB limit');
  }
  
  return {
    id: crypto.randomUUID(),
    file,
    name: file.name,
    size: file.size,
    type: file.type,
    uploadedAt: new Date(),
    isValid: validationErrors.length === 0,
    validationErrors: validationErrors.length > 0 ? validationErrors : undefined
  };
}

export function validateCompanyFile(file: File): UploadedFile {
  const validationErrors: string[] = [];
  
  // Check file extension
  const hasValidExtension = FILE_VALIDATION.company.allowedExtensions.some(ext => 
    file.name.toLowerCase().endsWith(ext)
  );
  if (!hasValidExtension) {
    validationErrors.push(FILE_VALIDATION.company.errorMessage);
  }
  
  // Check MIME type
  if (!FILE_VALIDATION.company.allowedMimeTypes.includes(file.type)) {
    validationErrors.push(FILE_VALIDATION.company.errorMessage);
  }
  
  // Check file size
  if (file.size > FILE_VALIDATION.company.maxSizeBytes) {
    validationErrors.push('File size exceeds 50MB limit');
  }
  
  return {
    id: crypto.randomUUID(),
    file,
    name: file.name,
    size: file.size,
    type: file.type,
    uploadedAt: new Date(),
    isValid: validationErrors.length === 0,
    validationErrors: validationErrors.length > 0 ? validationErrors : undefined
  };
}

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
```

### Step 7: Create Bank Upload Zone Component

Create `src/components/upload/BankUploadZone.tsx`:

```typescript
بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ

'use client';

import React from 'react';
import { useDropzone } from 'react-dropzone';
import { validateBankFile, formatFileSize } from '@/lib/file-utils';
import { THEME_COLORS } from '@/lib/constants';
import type { UploadedFile } from '@/types/upload';

interface BankUploadZoneProps {
  onFileUpload: (file: UploadedFile) => void;
  uploadedFile: UploadedFile | null;
}

export default function BankUploadZone({ onFileUpload, uploadedFile }: BankUploadZoneProps) {
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: { 'application/pdf': ['.pdf'] },
    maxFiles: 1,
    onDrop: (acceptedFiles, fileRejections) => {
      if (acceptedFiles.length > 0) {
        const validatedFile = validateBankFile(acceptedFiles[0]);
        onFileUpload(validatedFile);
      }
    }
  });

  return (
    <div
      {...getRootProps()}
      className={`
        rounded-2xl p-8 text-center cursor-pointer transition-all duration-200
        ${isDragActive ? 'scale-105' : 'scale-100'}
        ${uploadedFile?.isValid ? 'border-4 border-green-500' : 'border-4 border-dashed'}
      `}
      style={{
        backgroundColor: THEME_COLORS.uploadZone,
        borderColor: uploadedFile?.isValid ? THEME_COLORS.success : THEME_COLORS.uploadZoneHover
      }}
    >
      <input {...getInputProps()} />
      
      {/* Bank Icon/Logo */}
      <div className="mb-4">
        {/* Add bank SVG icon here */}
        <svg className="w-16 h-16 mx-auto text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
        </svg>
      </div>

      {uploadedFile ? (
        <div className="text-white">
          <p className="font-semibold text-lg">{uploadedFile.name}</p>
          <p className="text-sm opacity-90">{formatFileSize(uploadedFile.size)}</p>
        </div>
      ) : (
        <div className="text-white">
          <p className="font-semibold text-lg mb-2">
            {isDragActive ? 'Drop bank statement here' : 'Drag & drop bank statement'}
          </p>
          <p className="text-sm opacity-90">PDF files only</p>
        </div>
      )}

      {uploadedFile?.validationErrors && (
        <div className="mt-4 p-2 bg-red-500 rounded text-white text-sm">
          {uploadedFile.validationErrors[0]}
        </div>
      )}
    </div>
  );
}

وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
```

### Step 8: Create Company Upload Zone Component

Create `src/components/upload/CompanyUploadZone.tsx` (similar to BankUploadZone but for XLSX files):

```typescript
بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ

'use client';

import React from 'react';
import { useDropzone } from 'react-dropzone';
import { validateCompanyFile, formatFileSize } from '@/lib/file-utils';
import { THEME_COLORS } from '@/lib/constants';
import type { UploadedFile } from '@/types/upload';

interface CompanyUploadZoneProps {
  onFileUpload: (file: UploadedFile) => void;
  uploadedFile: UploadedFile | null;
}

export default function CompanyUploadZone({ onFileUpload, uploadedFile }: CompanyUploadZoneProps) {
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: { 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'] },
    maxFiles: 1,
    onDrop: (acceptedFiles) => {
      if (acceptedFiles.length > 0) {
        const validatedFile = validateCompanyFile(acceptedFiles[0]);
        onFileUpload(validatedFile);
      }
    }
  });

  return (
    <div
      {...getRootProps()}
      className={`
        rounded-2xl p-8 text-center cursor-pointer transition-all duration-200
        ${isDragActive ? 'scale-105' : 'scale-100'}
        ${uploadedFile?.isValid ? 'border-4 border-green-500' : 'border-4 border-dashed'}
      `}
      style={{
        backgroundColor: THEME_COLORS.uploadZone,
        borderColor: uploadedFile?.isValid ? THEME_COLORS.success : THEME_COLORS.uploadZoneHover
      }}
    >
      <input {...getInputProps()} />
      
      {/* Company Icon/Logo */}
      <div className="mb-4">
        <svg className="w-16 h-16 mx-auto text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
        </svg>
      </div>

      {uploadedFile ? (
        <div className="text-white">
          <p className="font-semibold text-lg">{uploadedFile.name}</p>
          <p className="text-sm opacity-90">{formatFileSize(uploadedFile.size)}</p>
        </div>
      ) : (
        <div className="text-white">
          <p className="font-semibold text-lg mb-2">
            {isDragActive ? 'Drop company data here' : 'Drag & drop company data'}
          </p>
          <p className="text-sm opacity-90">XLSX files only</p>
        </div>
      )}

      {uploadedFile?.validationErrors && (
        <div className="mt-4 p-2 bg-red-500 rounded text-white text-sm">
          {uploadedFile.validationErrors[0]}
        </div>
      )}
    </div>
  );
}

وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
```

### Step 9: Create Format Selector Component

Create `src/components/upload/FormatSelector.tsx`:

```typescript
بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ

'use client';

import React from 'react';
import { FORMAT_OPTIONS, type FormatOption } from '@/lib/constants';

interface FormatSelectorProps {
  value: FormatOption | null;
  onChange: (value: FormatOption) => void;
}

export default function FormatSelector({ value, onChange }: FormatSelectorProps) {
  return (
    <div className="w-full">
      <label className="block text-sm font-medium mb-2" style={{ color: '#2D2D2D' }}>
        Select Data Format
      </label>
      <select
        value={value || ''}
        onChange={(e) => onChange(e.target.value as FormatOption)}
        className="w-full p-3 rounded-lg border-2 focus:outline-none focus:ring-2"
        style={{ backgroundColor: '#FFFFFF', borderColor: '#FF6B6B' }}
      >
        <option value="">Choose format...</option>
        {FORMAT_OPTIONS.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </div>
  );
}

وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
```

### Step 10: Create Column Mapping Fields Component

Create `src/components/upload/ColumnMappingFields.tsx` (handles conditional field display):

```typescript
بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ

'use client';

import React from 'react';
import type { ColumnMappingConfiguration } from '@/types/upload';

interface ColumnMappingFieldsProps {
  config: ColumnMappingConfiguration;
  onChange: (config: ColumnMappingConfiguration) => void;
}

export default function ColumnMappingFields({ config, onChange }: ColumnMappingFieldsProps) {
  const handleFieldChange = (field: string, value: string) => {
    if (config.formatType === 'debit-plus-credit') {
      onChange({
        ...config,
        debitPlusCreditFields: {
          ...config.debitPlusCreditFields,
          [field]: value
        }
      });
    } else {
      onChange({
        ...config,
        debitPipeCreditFields: {
          ...config.debitPipeCreditFields,
          [field]: value
        }
      });
    }
  };

  return (
    <div className="space-y-4">
      {config.formatType === 'debit-plus-credit' ? (
        <>
          <input placeholder="Transaction Date Column" 
            value={config.debitPlusCreditFields?.transactionDateColumn || ''}
            onChange={(e) => handleFieldChange('transactionDateColumn', e.target.value)}
            className="w-full p-3 rounded-lg border-2"
          />
          <input placeholder="Debit Plus Credit Column"
            value={config.debitPlusCreditFields?.debitPlusCreditColumn || ''}
            onChange={(e) => handleFieldChange('debitPlusCreditColumn', e.target.value)}
            className="w-full p-3 rounded-lg border-2"
          />
          <input placeholder="Transaction Details Column"
            value={config.debitPlusCreditFields?.transactionDetailsColumn || ''}
            onChange={(e) => handleFieldChange('transactionDetailsColumn', e.target.value)}
            className="w-full p-3 rounded-lg border-2"
          />
        </>
      ) : (
        <>
          <input placeholder="Transaction Date Column"
            value={config.debitPipeCreditFields?.transactionDateColumn || ''}
            onChange={(e) => handleFieldChange('transactionDateColumn', e.target.value)}
            className="w-full p-3 rounded-lg border-2"
          />
          <input placeholder="Debit Column"
            value={config.debitPipeCreditFields?.debitColumn || ''}
            onChange={(e) => handleFieldChange('debitColumn', e.target.value)}
            className="w-full p-3 rounded-lg border-2"
          />
          <input placeholder="Credit Column"
            value={config.debitPipeCreditFields?.creditColumn || ''}
            onChange={(e) => handleFieldChange('creditColumn', e.target.value)}
            className="w-full p-3 rounded-lg border-2"
          />
          <input placeholder="Transaction Details Column"
            value={config.debitPipeCreditFields?.transactionDetailsColumn || ''}
            onChange={(e) => handleFieldChange('transactionDetailsColumn', e.target.value)}
            className="w-full p-3 rounded-lg border-2"
          />
        </>
      )}
    </div>
  );
}

وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
```

### Step 11: Create Main Upload Page

Create `src/app/upload/page.tsx`:

```typescript
بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ

'use client';

import React, { useState } from 'react';
import BankUploadZone from '@/components/upload/BankUploadZone';
import CompanyUploadZone from '@/components/upload/CompanyUploadZone';
import FormatSelector from '@/components/upload/FormatSelector';
import ColumnMappingFields from '@/components/upload/ColumnMappingFields';
import { THEME_COLORS } from '@/lib/constants';
import type { UploadedFile, ColumnMappingConfiguration } from '@/types/upload';

export default function UploadPage() {
  const [bankFile, setBankFile] = useState<UploadedFile | null>(null);
  const [companyFile, setCompanyFile] = useState<UploadedFile | null>(null);
  const [columnMapping, setColumnMapping] = useState<ColumnMappingConfiguration>({
    formatType: 'debit-plus-credit',
    isComplete: false
  });

  const handleSubmit = async () => {
    // Create FormData and submit to backend
    const formData = new FormData();
    if (bankFile && companyFile) {
      formData.append('bankStatement', bankFile.file);
      formData.append('companyData', companyFile.file);
      formData.append('formatType', columnMapping.formatType);
      // ... add column mapping fields
    }
  };

  return (
    <div className="min-h-screen" style={{ backgroundColor: THEME_COLORS.background }}>
      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
          <BankUploadZone onFileUpload={setBankFile} uploadedFile={bankFile} />
          <CompanyUploadZone onFileUpload={setCompanyFile} uploadedFile={companyFile} />
        </div>
        
        <FormatSelector 
          value={columnMapping.formatType}
          onChange={(value) => setColumnMapping({ ...columnMapping, formatType: value })}
        />
        
        <ColumnMappingFields 
          config={columnMapping}
          onChange={setColumnMapping}
        />
        
        <button onClick={handleSubmit} className="...">
          Submit for Processing
        </button>
      </div>
    </div>
  );
}

وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
```

### Step 12: Test the Implementation

```bash
# Start development server
npm run dev

# Open browser to http://localhost:3000/upload
# Test file uploads, format selection, and field validation
```

## Implementation Notes

**Constitutional Compliance**:
- All files start with `بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ`
- Critical logic sections marked with `وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ`
- All files end with `وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ`

**Component Order**: Implement components in the order listed above (Step 4-11) to avoid dependency issues.

**Styling**: Use the THEME_COLORS constant for consistent peach-red theme across all components.

**Next Steps**: After implementing all components, integrate with backend API for form submission.

## Troubleshooting

**Issue**: File upload not working  
**Solution**: Check that react-dropzone is properly installed and imported

**Issue**: ShadCN components not styling  
**Solution**: Ensure Tailwind CSS is properly configured in your project

**Issue**: TypeScript errors  
**Solution**: Make sure all type definitions are properly imported from `@/types/upload`

وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
