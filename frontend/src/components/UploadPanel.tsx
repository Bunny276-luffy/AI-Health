'use client';

import React, { useCallback, useRef, useState } from 'react';
import { Upload, FileImage, Loader2, X } from 'lucide-react';

interface UploadPanelProps {
  onScanUpload: (file: File, isBaseline: boolean) => void;
  isProcessing: boolean;
}

export function UploadPanel({ onScanUpload, isProcessing }: UploadPanelProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(
    (file: File) => {
      setUploadedFile(file);
      onScanUpload(file, false);
    },
    [onScanUpload]
  );

  const onDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const onDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const onDragLeave = () => setIsDragging(false);

  const onInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  };

  const clearFile = () => {
    setUploadedFile(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <div className="bg-slate-900 border border-slate-700 rounded-xl p-5 flex flex-col gap-4">
      <div className="flex items-center gap-2">
        <Upload className="text-violet-400" size={20} />
        <h3 className="text-slate-100 font-semibold text-sm">Upload Medical Scan</h3>
      </div>

      {/* Drop Zone */}
      <div
        onDrop={onDrop}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onClick={() => !isProcessing && fileInputRef.current?.click()}
        className={`
          relative border-2 border-dashed rounded-xl p-8 text-center cursor-pointer
          transition-all duration-200 flex flex-col items-center gap-3
          ${isDragging
            ? 'border-violet-500 bg-violet-500/10'
            : 'border-slate-700 hover:border-violet-600 hover:bg-violet-500/5'
          }
          ${isProcessing ? 'pointer-events-none opacity-60' : ''}
        `}
      >
        {isProcessing ? (
          <>
            <Loader2 size={32} className="text-violet-400 animate-spin" />
            <p className="text-sm text-slate-400">Analysing scan…</p>
            <p className="text-xs text-slate-600">Running 10-pass MC Dropout ensemble</p>
          </>
        ) : uploadedFile ? (
          <>
            <FileImage size={32} className="text-emerald-400" />
            <p className="text-sm text-slate-300 font-medium truncate max-w-full px-4">
              {uploadedFile.name}
            </p>
            <p className="text-xs text-slate-500">
              {(uploadedFile.size / 1024).toFixed(1)} KB — click to replace
            </p>
          </>
        ) : (
          <>
            <div className="w-14 h-14 bg-slate-800 rounded-full flex items-center justify-center border border-slate-700">
              <Upload size={24} className="text-slate-400" />
            </div>
            <div>
              <p className="text-sm text-slate-300 font-medium">
                Drop scan here or <span className="text-violet-400">click to browse</span>
              </p>
              <p className="text-xs text-slate-500 mt-1">
                Supports JPG, PNG, DICOM (.dcm) — max 50MB
              </p>
            </div>
          </>
        )}

        <input
          ref={fileInputRef}
          type="file"
          accept="image/*,.dcm"
          className="hidden"
          onChange={onInputChange}
        />
      </div>

      {/* Clear Button */}
      {uploadedFile && !isProcessing && (
        <button
          onClick={clearFile}
          className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-red-400 transition-colors self-start"
        >
          <X size={12} />
          Clear upload
        </button>
      )}

      {/* Format badges */}
      <div className="flex gap-2 flex-wrap">
        {['MRI', 'CT', 'PET', 'DICOM'].map((fmt) => (
          <span
            key={fmt}
            className="text-[10px] text-slate-500 border border-slate-800 px-2 py-0.5 rounded-full"
          >
            {fmt}
          </span>
        ))}
      </div>
    </div>
  );
}
