'use client';

import React, { useState } from 'react';
import axios from 'axios';
import { DashboardLayout } from '../components/DashboardLayout';
import { UploadPanel } from '../components/UploadPanel';
import { VisualizationPanel } from '../components/VisualizationPanel';
import { UncertaintyPanel } from '../components/UncertaintyPanel';
import { VQAPanel } from '../components/VQAPanel';
import { RadiomicsPanel } from '../components/RadiomicsPanel';
import { TemporalComparisonPanel } from '../components/TemporalComparisonPanel';
import { OrganSelector, OrganKey } from '../components/OrganSelector';
import { ConformalIntervalCard } from '../components/ConformalIntervalCard';
import { FileText, Cpu, CheckCircle } from 'lucide-react';
import toast from 'react-hot-toast';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// ---------------------------------------------------------------------------
// Types (strict — no `any`)
// ---------------------------------------------------------------------------

interface DicomMetadata {
  patient_age: string;
  modality: string;
  slice_thickness: string;
  dicom_valid: boolean;
}

interface ConformalResult {
  lower_bound: number;
  upper_bound: number;
  coverage: number;
  prediction_set: string[];
}

interface PredictionResult {
  has_tumor: boolean;
  tumor_probability: number;
  confidence_score: number;
}

interface UncertaintyResult {
  aleatoric: number;
  epistemic: number;
  total: number;
  is_high_uncertainty: boolean;
}

interface HeatmapPoint {
  x: number;
  y: number;
  value: number;
}

interface VisualizationResult {
  bounding_boxes: number[][];
  heatmap_data: HeatmapPoint[];
}

interface MetadataResult extends DicomMetadata {
  model_used: string;
  inference_time_ms: number;
  calibrated: boolean;
  registration_applied?: string;
  organ_label: string;
  organ: string;
}

interface AnalysisResults {
  prediction: PredictionResult;
  uncertainty: UncertaintyResult;
  conformal: ConformalResult;
  visualizations: VisualizationResult;
  metadata: MetadataResult;
}

interface RadiomicsFeature {
  name: string;
  value: number;
  unit: string;
  color: 'green' | 'amber' | 'red';
  high_desc: string;
  low_desc: string;
}

interface ControlAction {
  reanalysis_performed: boolean;
  message: string;
}

interface AnalyzeApiResponse {
  status: string;
  results: AnalysisResults;
  radiomics: RadiomicsFeature[];
  control_actions: ControlAction;
}

// ---------------------------------------------------------------------------
// Dashboard Page
// ---------------------------------------------------------------------------

export default function DashboardPage() {
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [currentScanUrl, setCurrentScanUrl] = useState<string | null>(null);
  const [currentFile, setCurrentFile] = useState<File | null>(null);
  const [results, setResults] = useState<AnalysisResults | null>(null);
  const [radiomics, setRadiomics] = useState<RadiomicsFeature[]>([]);
  const [controlAction, setControlAction] = useState<ControlAction | null>(null);
  const [selectedOrgan, setSelectedOrgan] = useState<OrganKey>('BRAIN');

  const handleScanUpload = async (file: File, isBaseline: boolean) => {
    if (isBaseline) return;

    setCurrentFile(file);
    setCurrentScanUrl(URL.createObjectURL(file));
    setIsProcessing(true);
    setResults(null);
    setRadiomics([]);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('auto_calibrate', 'false');
    formData.append('organ', selectedOrgan);

    try {
      const response = await axios.post<AnalyzeApiResponse>(
        `${API_BASE}/analyze`,
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      );
      setResults(response.data.results);
      setRadiomics(response.data.radiomics ?? []);
      setControlAction(response.data.control_actions);
    } catch (error) {
      console.error('Error analyzing scan', error);
      toast.error('Analysis failed. Is the backend running?');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleDownloadReport = async () => {
    if (!results) return;
    try {
      toast.loading('Generating Diagnostic Report…', { id: 'report' });
      const formData = new FormData();
      formData.append('results_json', JSON.stringify(results));

      const response = await axios.post(`${API_BASE}/report`, formData, {
        responseType: 'blob',
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'NeuroScan_Diagnostic_Report.pdf');
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
      toast.success('Report downloaded!', { id: 'report' });
    } catch {
      toast.error('Failed to generate report', { id: 'report' });
    }
  };

  // Build scan context for VQA
  const vqaScanContext = results
    ? {
        tumor_probability: results.prediction.tumor_probability,
        epistemic_uncertainty: results.uncertainty.epistemic,
        aleatoric_uncertainty: results.uncertainty.aleatoric,
        total_uncertainty: results.uncertainty.total,
        has_tumor: results.prediction.has_tumor,
        confidence_score: results.prediction.confidence_score,
        bounding_boxes: results.visualizations.bounding_boxes,
        dicom_metadata: {
          patient_age: results.metadata.patient_age,
          modality: results.metadata.modality,
          slice_thickness: results.metadata.slice_thickness,
          dicom_valid: results.metadata.dicom_valid,
        },
        organ: selectedOrgan,
      }
    : null;

  const organLabel = results?.metadata.organ_label ?? `NeuroScan — ${selectedOrgan.charAt(0) + selectedOrgan.slice(1).toLowerCase()} Tumor Detection`;

  return (
    <DashboardLayout>
      {/* Dynamic title bar */}
      <div className="mb-4">
        <h1 className="text-xl font-bold text-slate-100">
          NeuroScan —{' '}
          <span className="text-violet-400">{organLabel}</span>
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">
          MC Dropout · Conformal Prediction · SimpleITK · Radiomics · VQA
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column */}
        <div className="flex flex-col gap-6">
          {/* Organ Selector */}
          <div className="panel">
            <OrganSelector
              selectedOrgan={selectedOrgan}
              onOrganChange={setSelectedOrgan}
            />
          </div>

          <UploadPanel onScanUpload={handleScanUpload} isProcessing={isProcessing} />

          {/* System Status */}
          <div className="panel flex flex-col">
            <div className="panel-header">
              <Cpu className="text-emerald-400" size={20} />
              <h3 className="panel-title m-0">System Status</h3>
            </div>
            <div className="space-y-3">
              <div className="flex justify-between items-center text-sm">
                <span className="text-slate-400">Inference Engine</span>
                <span className="text-emerald-400 font-medium bg-emerald-400/10 px-2 py-0.5 rounded border border-emerald-400/20 text-xs">
                  Edge Optimized
                </span>
              </div>
              {results?.metadata && (
                <div className="flex justify-between items-center text-sm">
                  <span className="text-slate-400">Inference Time</span>
                  <span className="text-slate-200">{results.metadata.inference_time_ms} ms</span>
                </div>
              )}
              {controlAction?.reanalysis_performed && (
                <div className="mt-2 p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg text-xs text-blue-200">
                  <span className="block font-semibold text-blue-400 mb-1">
                    Self-Calibration Triggered
                  </span>
                  {controlAction.message}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Middle Column: Visualization */}
        <VisualizationPanel
          originalImageSrc={currentScanUrl}
          heatmapData={results?.visualizations?.heatmap_data ?? []}
          boundingBoxes={results?.visualizations?.bounding_boxes ?? []}
          isProcessing={isProcessing}
        />

        {/* Right Column: Uncertainty + Conformal */}
        <div className="flex flex-col gap-4">
          <UncertaintyPanel results={results} />
          <ConformalIntervalCard conformal={results?.conformal ?? null} />
        </div>
      </div>

      {/* Diagnostic Summary + Report */}
      <div className="panel mt-6 flex flex-col">
        <div className="panel-header justify-between">
          <div className="flex items-center gap-2">
            <FileText className="text-purple-400" size={20} />
            <h3 className="panel-title m-0">Diagnostic Summary</h3>
          </div>
          <button
            onClick={handleDownloadReport}
            className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-1.5 rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={!results || isProcessing}
          >
            Generate PDF Report
          </button>
        </div>

        <div className="flex-1 bg-slate-950/50 rounded-lg border border-slate-800 p-4 space-y-4">
          {!results ? (
            <p className="text-slate-500 italic text-sm">Summary will appear here after analysis.</p>
          ) : (
            <>
              <p className="text-slate-300 text-sm leading-relaxed">
                The deep learning MC Dropout ensemble processed this{' '}
                <strong className="text-slate-200">{selectedOrgan.toLowerCase()}</strong> scan
                over 10 parallel passes. Based on inference,{' '}
                <strong className={results.prediction.has_tumor ? 'text-red-400' : 'text-emerald-400'}>
                  {results.prediction.has_tumor
                    ? 'an anomalous lesion was detected'
                    : 'no significant anomalies were detected'}
                </strong>.
              </p>

              {results.uncertainty.epistemic > 30.0 && (
                <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-md">
                  <span className="text-red-400 text-sm font-bold block mb-1">
                    ⚠️ Clinical Warning Triggered
                  </span>
                  <span className="text-red-300 text-xs">
                    Epistemic Uncertainty exceeded 30% ({results.uncertainty.epistemic}%).
                    SimpleITK Image Registration was automatically applied to stabilise the
                    prediction. Manual review required.
                  </span>
                </div>
              )}

              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-slate-900 border border-slate-800 p-3 rounded-lg">
                  <span className="block text-xs text-slate-500 mb-1">Tumor Probability</span>
                  <span className="text-lg font-bold text-slate-200">
                    {results.prediction.tumor_probability}%
                  </span>
                </div>

                {/* Conformal interval replaces raw confidence */}
                <div className="bg-slate-900 border border-slate-800 p-3 rounded-lg">
                  <span className="block text-xs text-slate-500 mb-1">Conformal Interval</span>
                  <span className="text-sm font-bold text-indigo-300">
                    [{(results.conformal.lower_bound * 100).toFixed(1)}%,{' '}
                    {(results.conformal.upper_bound * 100).toFixed(1)}%]
                  </span>
                </div>

                <div className="bg-slate-900 border border-slate-800 p-3 rounded-lg">
                  <span className="block text-xs text-slate-500 mb-1">Total Uncertainty</span>
                  <span className="text-lg font-bold text-slate-200">
                    {results.uncertainty.total}%
                  </span>
                </div>

                <div className="bg-slate-900 border border-slate-800 p-3 rounded-lg">
                  <span className="block text-xs text-slate-500 mb-1">Calibration Node</span>
                  <span className="text-lg font-bold text-slate-200 flex items-center gap-2">
                    {results.metadata.calibrated ? (
                      <>
                        <CheckCircle size={16} className="text-emerald-500" /> Active
                      </>
                    ) : (
                      <span className="text-slate-500">Idle</span>
                    )}
                  </span>
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Radiomics Panel */}
      <div className="mt-6">
        <RadiomicsPanel features={radiomics} />
      </div>

      {/* VQA Panel */}
      <div className="mt-6">
        <VQAPanel scanContext={vqaScanContext} apiBase={API_BASE} />
      </div>

      {/* Temporal Comparison Panel */}
      <div className="mt-6">
        <TemporalComparisonPanel apiBase={API_BASE} />
      </div>
    </DashboardLayout>
  );
}
