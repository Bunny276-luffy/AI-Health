'use client';

import React from 'react';
import { Activity } from 'lucide-react';

interface RadiomicsFeature {
  name: string;
  value: number;
  unit: string;
  color: 'green' | 'amber' | 'red';
  high_desc: string;
  low_desc: string;
}

interface RadiomicsPanelProps {
  features: RadiomicsFeature[];
}

const COLOR_MAP: Record<string, { bg: string; border: string; text: string; badge: string }> = {
  green: { bg: 'bg-emerald-500/5', border: 'border-emerald-500/20', text: 'text-emerald-400', badge: 'bg-emerald-500/20 text-emerald-300' },
  amber: { bg: 'bg-amber-500/5', border: 'border-amber-500/20', text: 'text-amber-400', badge: 'bg-amber-500/20 text-amber-300' },
  red: { bg: 'bg-red-500/5', border: 'border-red-500/20', text: 'text-red-400', badge: 'bg-red-500/20 text-red-300' },
};

const LABEL_MAP: Record<string, string> = { green: 'Normal', amber: 'Borderline', red: 'Abnormal' };

const FeatureCard: React.FC<{ feature: RadiomicsFeature }> = ({ feature }) => {
  const colors = COLOR_MAP[feature.color] ?? COLOR_MAP.amber;
  const label = LABEL_MAP[feature.color] ?? 'Borderline';
  const clinicalNote = feature.color === 'red' ? feature.high_desc : feature.low_desc;

  return (
    <div className={`rounded-lg border p-3 flex flex-col gap-1 ${colors.bg} ${colors.border}`}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-slate-300">{feature.name}</span>
        <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded-full ${colors.badge}`}>{label}</span>
      </div>
      <span className={`text-lg font-bold tabular-nums ${colors.text}`}>
        {feature.value.toFixed(4)}
        {feature.unit && feature.unit !== '—' && <span className="text-xs font-normal text-slate-500 ml-1">{feature.unit}</span>}
      </span>
      <p className="text-[10px] text-slate-500 leading-tight line-clamp-2">{clinicalNote}</p>
    </div>
  );
};

export const RadiomicsPanel: React.FC<RadiomicsPanelProps> = ({ features }) => {
  if (!features || features.length === 0) {
    return (
      <div className="bg-slate-900 border border-slate-700 rounded-xl p-5">
        <div className="flex items-center gap-2 mb-3">
          <Activity className="text-cyan-400" size={20} />
          <h3 className="text-slate-100 font-semibold text-sm">Radiomics Analysis</h3>
        </div>
        <p className="text-slate-500 text-xs italic">Radiomics features will appear here after analysis.</p>
      </div>
    );
  }

  const abnormalCount = features.filter((f) => f.color === 'red').length;
  const borderlineCount = features.filter((f) => f.color === 'amber').length;

  return (
    <div className="bg-slate-900 border border-slate-700 rounded-xl p-5 flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity className="text-cyan-400" size={20} />
          <h3 className="text-slate-100 font-semibold text-sm">Radiomics Analysis</h3>
        </div>
        <div className="flex gap-2 text-[10px]">
          {abnormalCount > 0 && <span className="bg-red-500/20 text-red-300 px-2 py-0.5 rounded-full">{abnormalCount} Abnormal</span>}
          {borderlineCount > 0 && <span className="bg-amber-500/20 text-amber-300 px-2 py-0.5 rounded-full">{borderlineCount} Borderline</span>}
        </div>
      </div>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {features.map((feature) => <FeatureCard key={feature.name} feature={feature} />)}
      </div>
      <p className="text-[10px] text-slate-600">
        Features computed from the tumor ROI probability map via first-order statistics and GLCM analysis.
      </p>
    </div>
  );
};
