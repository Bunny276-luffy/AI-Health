'use client';

import React from 'react';
import { Brain, Wind, Activity, Target } from 'lucide-react';

export type OrganKey = 'BRAIN' | 'LUNG' | 'LIVER' | 'PROSTATE';

const ORGAN_OPTIONS = [
  { key: 'BRAIN' as OrganKey, label: 'Brain', subtitle: 'Tumour Segmentation', icon: <Brain size={18} />, accent: 'violet' },
  { key: 'LUNG' as OrganKey, label: 'Lung', subtitle: 'Nodule Detection', icon: <Wind size={18} />, accent: 'sky' },
  { key: 'LIVER' as OrganKey, label: 'Liver', subtitle: 'Lesion Mapping', icon: <Activity size={18} />, accent: 'amber' },
  { key: 'PROSTATE' as OrganKey, label: 'Prostate', subtitle: 'Cancer Screening', icon: <Target size={18} />, accent: 'rose' },
];

const ACCENT_CLASSES: Record<string, { selected: string; hover: string; ring: string }> = {
  violet: { selected: 'bg-violet-600/20 border-violet-500 text-violet-300', hover: 'hover:border-violet-600 hover:bg-violet-600/10', ring: 'ring-violet-500/30' },
  sky: { selected: 'bg-sky-600/20 border-sky-500 text-sky-300', hover: 'hover:border-sky-600 hover:bg-sky-600/10', ring: 'ring-sky-500/30' },
  amber: { selected: 'bg-amber-600/20 border-amber-500 text-amber-300', hover: 'hover:border-amber-600 hover:bg-amber-600/10', ring: 'ring-amber-500/30' },
  rose: { selected: 'bg-rose-600/20 border-rose-500 text-rose-300', hover: 'hover:border-rose-600 hover:bg-rose-600/10', ring: 'ring-rose-500/30' },
};

export const OrganSelector: React.FC<{ selectedOrgan: OrganKey; onOrganChange: (o: OrganKey) => void }> = ({ selectedOrgan, onOrganChange }) => {
  return (
    <div className="flex flex-col gap-2">
      <label className="text-xs text-slate-400 font-medium uppercase tracking-wide">Target Organ</label>
      <div className="grid grid-cols-2 gap-2">
        {ORGAN_OPTIONS.map((option) => {
          const isSelected = selectedOrgan === option.key;
          const colors = ACCENT_CLASSES[option.accent];
          return (
            <button
              key={option.key} onClick={() => onOrganChange(option.key)}
              className={`flex items-center gap-2.5 px-3 py-2.5 rounded-lg border text-left transition-all duration-150 ${isSelected ? `${colors.selected} ring-1 ${colors.ring} shadow-sm` : `bg-slate-800/50 border-slate-700 text-slate-400 ${colors.hover}`}`}
            >
              <span className={isSelected ? '' : 'opacity-60'}>{option.icon}</span>
              <div className="flex flex-col min-w-0">
                <span className="text-xs font-semibold leading-tight">{option.label}</span>
                <span className="text-[10px] opacity-70 leading-tight truncate">{option.subtitle}</span>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};
