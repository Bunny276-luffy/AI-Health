'use client';

import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { UploadCloud, FileImage, X, Activity } from 'lucide-react';
import clsx from 'clsx';
import toast from 'react-hot-toast';

interface UploadPanelProps {
  onScanUpload: (file: File, isBaseline: boolean) => void;
  isProcessing: boolean;
}

export function UploadPanel({ onScanUpload, isProcessing }: UploadPanelProps) {
  const [mode, setMode] = useState<'current' | 'progression'>('current');
  
  const [currentFile, setCurrentFile] = useState<File | null>(null);
  const [baselineFile, setBaselineFile] = useState<File | null>(null);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;
    
    const file = acceptedFiles[0];
    
    if (mode === 'current') {
      setCurrentFile(file);
      onScanUpload(file, false);
      toast.success("Scan loaded successfully");
    } else {
      // Logic for baseline vs current
      if (!currentFile) {
        setCurrentFile(file);
        toast.success("Loaded Current Scan. Now upload Baseline Scan.");
      } else {
        setBaselineFile(file);
        onScanUpload(file, true); 
        toast.success("Loaded Baseline Scan.");
      }
    }
  }, [mode, currentFile, onScanUpload]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg', '.dcm', '.dicom'],
    },
    maxFiles: 1,
    disabled: isProcessing
  });

  return (
    <div className="panel flex flex-col h-full">
      <div className="panel-header">
        <UploadCloud className="text-blue-500" size={20} />
        <h3 className="panel-title text-base m-0">Image Upload</h3>
        
        <div className="ml-auto flex bg-slate-950 rounded-lg p-1 border border-slate-800">
          <button 
            type="button"
            onClick={() => setMode('current')}
            className={clsx(
              "px-3 py-1 text-xs font-medium rounded-md transition-colors",
              mode === 'current' ? "bg-slate-800 text-white" : "text-slate-400 hover:text-slate-200"
            )}
          >
            Single Scan
          </button>
          <button 
            type="button"
            onClick={() => { setMode('progression'); setCurrentFile(null); setBaselineFile(null); }}
            className={clsx(
              "px-3 py-1 text-xs font-medium rounded-md transition-colors",
              mode === 'progression' ? "bg-slate-800 text-white" : "text-slate-400 hover:text-slate-200"
            )}
          >
            Progression
          </button>
        </div>
      </div>

      <div 
        {...getRootProps()} 
        className={clsx(
          "flex-1 border-2 border-dashed rounded-xl flex flex-col items-center justify-center p-6 text-center transition-all cursor-pointer relative overflow-hidden",
          isDragActive 
            ? "border-blue-500 bg-blue-500/5" 
            : "border-slate-700 hover:border-blue-500/50 hover:bg-slate-800/30",
          isProcessing && "opacity-50 pointer-events-none"
        )}
      >
        <input {...getInputProps()} />
        
        <FileImage size={40} className={clsx("mb-4 transition-colors", isDragActive ? "text-blue-500" : "text-slate-500")} />
        
        {mode === 'current' && !currentFile ? (
          <>
            <p className="text-sm font-medium text-slate-300 mb-1">
              Drag & drop medical scan here
            </p>
            <p className="text-xs text-slate-500">
              Supported: PNG, JPEG, DICOM
            </p>
          </>
        ) : mode === 'progression' && !currentFile ? (
          <>
            <p className="text-sm font-medium text-slate-300 mb-1">
              Step 1: Upload <span className="text-blue-400">Current</span> Scan
            </p>
          </>
        ) : mode === 'progression' && currentFile && !baselineFile ? (
          <>
            <p className="text-sm font-medium text-slate-300 mb-1">
              Step 2: Upload <span className="text-purple-400">Baseline/Previous</span> Scan
            </p>
          </>
        ) : (
          <div className="flex flex-col items-center space-y-2">
            <span className="text-sm text-green-400 font-medium">Files Ready</span>
            {currentFile && <span className="text-xs text-slate-400 bg-slate-900 px-2 py-1 rounded">Current: {currentFile.name}</span>}
            {baselineFile && <span className="text-xs text-slate-400 bg-slate-900 px-2 py-1 rounded">Baseline: {baselineFile.name}</span>}
          </div>
        )}

        {isProcessing && (
          <div className="absolute inset-0 bg-slate-900/80 backdrop-blur-sm flex flex-col items-center justify-center">
            <Activity className="animate-pulse text-blue-500 mb-3" size={32} />
            <span className="text-sm font-medium text-blue-400">Processing Scan Pipeline...</span>
          </div>
        )}
      </div>
    </div>
  );
}
