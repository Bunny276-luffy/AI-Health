'use client';

import React from 'react';
import { AlertCircle, Target, Activity } from 'lucide-react';
import clsx from 'clsx';
// Use dynamic import for recharts in the future, for now simple styled bars

interface MetricProps {
    label: string;
    value: number;
    type: 'success' | 'warning' | 'danger' | 'info';
    desc?: string;
}

const colors = {
    success: 'bg-emerald-500',
    warning: 'bg-amber-500',
    danger: 'bg-red-500',
    info: 'bg-blue-500',
};

const textColors = {
    success: 'text-emerald-400',
    warning: 'text-amber-400',
    danger: 'text-red-400',
    info: 'text-blue-400',
};

function MetricBar({ label, value, type, desc }: MetricProps) {
    return (
        <div className="mb-5 last:mb-0">
            <div className="flex justify-between items-center mb-1.5">
                <span className="text-sm font-medium text-slate-300">{label}</span>
                <span className={clsx("text-lg font-bold", textColors[type])}>{value.toFixed(1)}%</span>
            </div>
            <div className="w-full bg-slate-950 h-2.5 rounded-full overflow-hidden border border-slate-800">
                <div
                    className={clsx("h-full transition-all duration-1000 ease-out", colors[type])}
                    style={{ width: `${value}%` }}
                />
            </div>
            {desc && <p className="text-xs text-slate-500 mt-1.5">{desc}</p>}
        </div>
    );
}

export function UncertaintyPanel({ results }: { results: any }) {
    if (!results) {
        return (
            <div className="panel flex flex-col justify-center items-center h-full min-h-[300px] text-slate-500">
                <Activity size={32} className="mb-2 opacity-50" />
                <p className="text-sm">Awaiting Inference Results</p>
            </div>
        );
    }

    const { prediction, uncertainty } = results;

    return (
        <div className="panel flex flex-col h-full">
            <div className="panel-header">
                <Target className="text-indigo-400" size={20} />
                <h3 className="panel-title m-0">Uncertainty Estimation</h3>
            </div>

            <div className="flex-1 space-y-2 mt-2">
                <MetricBar
                    label="Prediction Confidence"
                    value={prediction?.confidence_score || 0}
                    type={prediction?.confidence_score > 80 ? 'success' : 'warning'}
                />

                <div className="pt-4 border-t border-slate-800">
                    <MetricBar
                        label="Aleatoric Uncertainty"
                        value={uncertainty?.aleatoric || 0}
                        type={uncertainty?.aleatoric > 20 ? 'danger' : 'info'}
                        desc="Inherent data noise (e.g. scan artifacts, low contrast)."
                    />
                    <MetricBar
                        label="Epistemic Uncertainty"
                        value={uncertainty?.epistemic || 0}
                        type={uncertainty?.epistemic > 20 ? 'warning' : 'info'}
                        desc="Model ignorance (out-of-distribution detection)."
                    />
                </div>

                {uncertainty?.is_high_uncertainty && (
                    <div className="mt-6 bg-amber-500/10 border border-amber-500/20 rounded-lg p-3 flex gap-3">
                        <AlertCircle className="text-amber-500 shrink-0" size={20} />
                        <div>
                            <h4 className="text-sm font-semibold text-amber-400">High Uncertainty Detected</h4>
                            <p className="text-xs text-amber-500/80 mt-1">
                                The model lacks sufficient confidence or data quality. Clinical review highly recommended.
                            </p>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
