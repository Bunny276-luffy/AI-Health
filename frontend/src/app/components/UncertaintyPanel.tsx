'use client';

import React from 'react';
import { ShieldAlert, Info } from 'lucide-react';

interface UncertaintyResult {
  aleatoric: number;
  epistemic: number;
  total: number;
  is_high_uncertainty: boolean;
}

interface UncertaintyPanelProps {
  results: { uncertainty: UncertaintyResult } | null;
}

export function UncertaintyPanel({ results }: UncertaintyPanelProps) {
  const unc = results?.uncertainty;

  return (
    <div className="panel flex flex-col h-full">
      <div className="panel-header">
        <ShieldAlert className="text-rose-400" size={20} />
        <h3 className="panel-title m-0">Uncertainty Estimation</h3>
      </div>
      
      {!unc ? (
        <div className="flex-1 flex items-center justify-center min-h-[120px]">
          <p className="text-sm text-slate-500 italic">No data yet</p>
        </div>
      ) : (
        <div className="space-y-5 flex-1">
          {/* Epistemic */}
          <div className="space-y-2">
            <div className="flex justify-between items-end">
              <div>
                <span className="block text-xs font-semibold text-slate-300">Epistemic Uncertainty</span>
                <span className="text-[10px] text-slate-500">Model knowledge gap</span>
              </div>
              <span className="text-sm font-bold text-rose-400">{unc.epistemic.toFixed(1)}%</span>
            </div>
            <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-rose-600 to-rose-400 rounded-full"
                style={{ width: `${Math.min(100, unc.epistemic)}%` }}
              />
            </div>
          </div>

          {/* Aleatoric */}
          <div className="space-y-2">
            <div className="flex justify-between items-end">
              <div>
                <span className="block text-xs font-semibold text-slate-300">Aleatoric Uncertainty</span>
                <span className="text-[10px] text-slate-500">Data noise & artifacts</span>
              </div>
              <span className="text-sm font-bold text-amber-400">{unc.aleatoric.toFixed(1)}%</span>
            </div>
            <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-amber-600 to-amber-400 rounded-full"
                style={{ width: `${Math.min(100, unc.aleatoric)}%` }}
              />
            </div>
          </div>

          <div className="pt-3 border-t border-slate-800 flex items-start gap-2">
            <Info size={14} className="text-slate-500 mt-0.5 shrink-0" />
            <p className="text-[10px] text-slate-400 leading-tight">
              Derived from 10-pass MC Dropout ensemble variance. High epistemic variance ({'>'}30%) triggers automatic SimpleITK registration.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
