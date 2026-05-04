'use client';

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { GitCompare, TrendingUp, TrendingDown, Minus, Calendar } from 'lucide-react';
import axios from 'axios';

interface HeatmapPoint { x: number; y: number; value: number; }
interface ScanResult {
  prediction: { has_tumor: boolean; tumor_probability: number };
  heatmap_data: HeatmapPoint[];
  bounding_boxes: number[][];
}
interface ComparisonMetrics {
  probability_delta: number;
  volume_delta_percent: number;
  uncertainty_delta: number;
  vdt_days: number | null;
  vdt_interpretation: string | null;
  severity: 'stable' | 'moderate' | 'critical';
}
interface CompareResponse { status: string; scan_a: ScanResult; scan_b: ScanResult; metrics: ComparisonMetrics; }

const SEVERITY_COLORS = {
  stable: { text: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/20' },
  moderate: { text: 'text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/20' },
  critical: { text: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/20' },
};

function DeltaArrow({ value }: { value: number }) {
  if (Math.abs(value) < 0.5) return <Minus size={14} className="text-slate-400" />;
  return value > 0 ? <TrendingUp size={14} className="text-red-400" /> : <TrendingDown size={14} className="text-emerald-400" />;
}

function HeatmapCanvas({ imageFile, heatmapPoints, boundingBoxes, label }: { imageFile: File | null; heatmapPoints: HeatmapPoint[]; boundingBoxes: number[][]; label: string; }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const draw = useCallback(() => {
    const canvas = canvasRef.current; if (!canvas) return;
    const ctx = canvas.getContext('2d'); if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const drawOverlay = () => {
      const { width: W, height: H } = canvas;
      for (const pt of heatmapPoints) {
        const x = pt.x * W; const y = pt.y * H; const r = Math.max(4, pt.value * 14);
        const grad = ctx.createRadialGradient(x, y, 0, x, y, r);
        grad.addColorStop(0, `rgba(239,68,68,${Math.min(0.7, pt.value)})`);
        grad.addColorStop(1, 'rgba(239,68,68,0)');
        ctx.fillStyle = grad; ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill();
      }
      ctx.strokeStyle = '#f87171'; ctx.lineWidth = 2;
      for (const box of boundingBoxes) ctx.strokeRect(box[0] * W, box[1] * H, box[2] * W, box[3] * H);
    };
    if (imageFile) {
      const img = new Image(); img.src = URL.createObjectURL(imageFile);
      img.onload = () => { ctx.drawImage(img, 0, 0, canvas.width, canvas.height); drawOverlay(); };
    } else {
      ctx.fillStyle = '#0f172a'; ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = '#334155'; ctx.font = '12px sans-serif'; ctx.textAlign = 'center'; ctx.fillText('No scan uploaded', canvas.width / 2, canvas.height / 2);
    }
  }, [imageFile, heatmapPoints, boundingBoxes]);
  useEffect(() => { draw(); }, [draw]);

  return (
    <div className="flex flex-col gap-1">
      <span className="text-xs text-slate-400 font-medium">{label}</span>
      <canvas ref={canvasRef} width={256} height={256} className="w-full aspect-square rounded-lg border border-slate-700 object-cover" />
    </div>
  );
}

export const TemporalComparisonPanel: React.FC<{ apiBase: string }> = ({ apiBase }) => {
  const [scanA, setScanA] = useState<File | null>(null); const [scanB, setScanB] = useState<File | null>(null);
  const [dateA, setDateA] = useState(''); const [dateB, setDateB] = useState('');
  const [result, setResult] = useState<CompareResponse | null>(null);
  const [loading, setLoading] = useState(false); const [error, setError] = useState('');

  const handleCompare = async () => {
    if (!scanA || !scanB) { setError('Please upload both scans.'); return; }
    setLoading(true); setError(''); setResult(null);
    const formData = new FormData(); formData.append('scan_a', scanA); formData.append('scan_b', scanB);
    if (dateA) formData.append('timestamp_a', dateA); if (dateB) formData.append('timestamp_b', dateB);
    try {
      const res = await axios.post<CompareResponse>(`${apiBase}/compare`, formData, { headers: { 'Content-Type': 'multipart/form-data' } });
      setResult(res.data);
    } catch { setError('Comparison failed. Check backend connection.'); } finally { setLoading(false); }
  };

  const metrics = result?.metrics; const sevColors = SEVERITY_COLORS[metrics?.severity ?? 'stable'];

  return (
    <div className="bg-slate-900 border border-slate-700 rounded-xl p-5 flex flex-col gap-5">
      <div className="flex items-center gap-2"><GitCompare className="text-sky-400" size={20} /><h3 className="text-slate-100 font-semibold text-sm">Temporal Scan Comparison</h3></div>
      <div className="grid grid-cols-2 gap-4">
        {(['a', 'b'] as const).map((side) => {
          const file = side === 'a' ? scanA : scanB; const setFile = side === 'a' ? setScanA : setScanB;
          const date = side === 'a' ? dateA : dateB; const setDate = side === 'a' ? setDateA : setDateB;
          const label = side === 'a' ? 'Baseline Scan' : 'Follow-up Scan';
          return (
            <div key={side} className="flex flex-col gap-2">
              <label className="text-xs text-slate-400 font-medium flex items-center gap-1"><span className={`w-2 h-2 rounded-full ${side === 'a' ? 'bg-sky-400' : 'bg-violet-400'}`} />{label}</label>
              <label className="cursor-pointer bg-slate-800 border border-dashed border-slate-600 hover:border-sky-500 rounded-lg p-3 text-center transition-colors">
                <input type="file" accept="image/*,.dcm" className="hidden" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
                <span className="text-xs text-slate-400">{file ? file.name : 'Click to upload'}</span>
              </label>
              <div className="flex items-center gap-1.5"><Calendar size={12} className="text-slate-500" />
                <input type="date" value={date} onChange={(e) => setDate(e.target.value)} className="flex-1 bg-slate-800 border border-slate-700 rounded px-2 py-1 text-xs text-slate-300 focus:outline-none focus:ring-1 focus:ring-sky-500" />
              </div>
            </div>
          );
        })}
      </div>
      <button onClick={handleCompare} disabled={!scanA || !scanB || loading} className="w-full bg-sky-600 hover:bg-sky-500 disabled:opacity-40 disabled:cursor-not-allowed text-white py-2 rounded-lg text-sm font-medium transition-colors">
        {loading ? 'Comparing…' : 'Run Temporal Comparison'}
      </button>
      {error && <p className="text-red-400 text-xs">{error}</p>}
      {result && (
        <div className="flex flex-col gap-4">
          <div className="grid grid-cols-2 gap-3">
            <HeatmapCanvas imageFile={scanA} heatmapPoints={result.scan_a.heatmap_data} boundingBoxes={result.scan_a.bounding_boxes} label={`Baseline — ${result.scan_a.prediction.tumor_probability}% prob.`} />
            <HeatmapCanvas imageFile={scanB} heatmapPoints={result.scan_b.heatmap_data} boundingBoxes={result.scan_b.bounding_boxes} label={`Follow-up — ${result.scan_b.prediction.tumor_probability}% prob.`} />
          </div>
          <div className={`rounded-lg border p-4 ${sevColors.bg} ${sevColors.border}`}>
            <p className={`text-xs font-bold mb-3 ${sevColors.text} uppercase tracking-wide`}>Progression Assessment — {metrics?.severity}</p>
            <div className="grid grid-cols-3 gap-3">
              {[{ label: 'Probability Δ', value: metrics?.probability_delta, suffix: '%' }, { label: 'Volume Δ', value: metrics?.volume_delta_percent, suffix: '%' }, { label: 'Uncertainty Δ', value: metrics?.uncertainty_delta, suffix: '%' }].map(({ label, value, suffix }) => (
                <div key={label} className="flex flex-col gap-1">
                  <span className="text-[10px] text-slate-400">{label}</span>
                  <span className={`text-base font-bold flex items-center gap-1 ${value && value > 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                    <DeltaArrow value={value ?? 0} />{value !== undefined ? `${value > 0 ? '+' : ''}${value}${suffix}` : 'N/A'}
                  </span>
                </div>
              ))}
            </div>
            {metrics?.vdt_interpretation && (
              <div className="mt-3 pt-3 border-t border-slate-700">
                <span className="text-[10px] text-slate-400 block mb-0.5">Volume Doubling Time</span><span className={`text-xs font-semibold ${sevColors.text}`}>{metrics.vdt_interpretation}</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
