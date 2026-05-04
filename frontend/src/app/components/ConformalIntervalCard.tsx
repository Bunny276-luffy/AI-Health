'use client';

import React, { useState } from 'react';
import { Shield, HelpCircle } from 'lucide-react';

interface ConformalResult { lower_bound: number; upper_bound: number; coverage: number; prediction_set: string[]; }

function InfoTooltip() {
  const [open, setOpen] = useState(false);
  return (
    <div className="relative inline-flex">
      <button onMouseEnter={() => setOpen(true)} onMouseLeave={() => setOpen(false)} className="text-slate-500 hover:text-slate-300 transition-colors"><HelpCircle size={13} /></button>
      {open && (
        <div className="absolute bottom-full right-0 mb-1.5 w-64 bg-slate-800 border border-slate-600 rounded-lg p-3 text-[10px] text-slate-300 leading-relaxed shadow-xl z-50">
          Conformal Prediction provides a mathematically guaranteed interval: with 90% statistical coverage, the true tumor probability lies within [lower_bound, upper_bound]. Unlike raw confidence, this interval is calibrated on a held-out set — making it statistically trustworthy.
          <div className="absolute bottom-0 right-2 translate-y-full border-x-4 border-t-4 border-x-transparent border-t-slate-600" />
        </div>
      )}
    </div>
  );
}

export const ConformalIntervalCard: React.FC<{ conformal: ConformalResult | null }> = ({ conformal }) => {
  if (!conformal) {
    return (
      <div className="bg-slate-900 border border-slate-700 rounded-lg p-3">
        <span className="block text-xs text-slate-500 mb-1">Conformal Interval</span><span className="text-slate-600 text-sm italic">Awaiting analysis…</span>
      </div>
    );
  }

  const lower = (conformal.lower_bound * 100).toFixed(1);
  const upper = (conformal.upper_bound * 100).toFixed(1);
  const coveragePct = Math.round(conformal.coverage * 100);
  const intervalWidth = conformal.upper_bound - conformal.lower_bound;
  const uncertainty_level = intervalWidth < 0.15 ? 'Tight' : intervalWidth < 0.30 ? 'Moderate' : 'Wide';
  const uncertainty_color = intervalWidth < 0.15 ? 'text-emerald-400' : intervalWidth < 0.30 ? 'text-amber-400' : 'text-red-400';

  return (
    <div className="bg-slate-900 border border-slate-700 rounded-lg p-3 flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5"><Shield size={12} className="text-indigo-400" /><span className="text-xs text-slate-400">Conformal Interval</span></div>
        <InfoTooltip />
      </div>
      <div className="flex items-baseline gap-1"><span className="text-lg font-bold text-slate-100 tabular-nums">[{lower}%, {upper}%]</span></div>
      <div className="flex items-center justify-between">
        <span className="text-[10px] bg-indigo-500/20 text-indigo-300 border border-indigo-500/20 px-1.5 py-0.5 rounded-full">{coveragePct}% statistically guaranteed</span>
        <span className={`text-[10px] font-semibold ${uncertainty_color}`}>{uncertainty_level} interval</span>
      </div>
      {conformal.prediction_set.length > 0 && (
        <div className="flex gap-1 flex-wrap">
          {conformal.prediction_set.map((cls) => (
            <span key={cls} className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${cls === 'TUMOR' ? 'bg-red-500/20 text-red-300' : 'bg-emerald-500/20 text-emerald-300'}`}>{cls}</span>
          ))}
          <span className="text-[10px] text-slate-500">in prediction set</span>
        </div>
      )}
    </div>
  );
};
