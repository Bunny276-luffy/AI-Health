'use client';

import React, { useState } from 'react';
import axios from 'axios';
import { DashboardLayout } from '../components/DashboardLayout';
import { UploadPanel } from '../components/UploadPanel';
import { VisualizationPanel } from '../components/VisualizationPanel';
import { UncertaintyPanel } from '../components/UncertaintyPanel';
import { FileText, Cpu, CheckCircle } from 'lucide-react';
import toast from 'react-hot-toast';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export default function DashboardPage() {
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentScanUrl, setCurrentScanUrl] = useState<string | null>(null);

  const [results, setResults] = useState<any>(null);
  const [controlAction, setControlAction] = useState<any>(null);

  const handleScanUpload = async (file: File, isBaseline: boolean) => {
    if (!isBaseline) {
      // Create local URL for preview immediately
      const url = URL.createObjectURL(file);
      setCurrentScanUrl(url);

      // Start processing pipeline
      setIsProcessing(true);

      const formData = new FormData();
      formData.append('file', file);
      // Automatically test the self-calibrating control loop flag
      formData.append('auto_calibrate', 'false');

      try {
        const response = await axios.post(`${API_BASE}/analyze`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });

        console.log("Analysis Results:", response.data);
        setResults(response.data.results);
        setControlAction(response.data.control_actions);

      } catch (error) {
        console.error("Error analyzing scan", error);
      } finally {
        setIsProcessing(false);
      }
    } else {
      console.log("Handle Progression Baseline...");
      // For a massive app we'd dispatch to the /progression endpoint here
      setIsProcessing(false);
    }
  };

  const handleDownloadReport = async () => {
    if (!results) return;
    try {
      toast.loading("Generating Diagnostic Report...", { id: "report" });
      const formData = new FormData();
      formData.append('results_json', JSON.stringify(results));

      const response = await axios.post(`${API_BASE}/report`, formData, {
        responseType: 'blob'
      });

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'NeuroScan_Diagnostic_Report.pdf');
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);

      toast.success("Report downloaded successfully!", { id: "report" });
    } catch (error) {
      console.error("Error generating report", error);
      toast.error("Failed to generate report", { id: "report" });
    }
  };

  return (
    <DashboardLayout>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Left Column: Upload & Control Logic */}
        <div className="flex flex-col gap-6">
          <UploadPanel onScanUpload={handleScanUpload} isProcessing={isProcessing} />

          {/* Edge/Diagnostic Status */}
          <div className="panel flex flex-col">
            <div className="panel-header">
              <Cpu className="text-emerald-400" size={20} />
              <h3 className="panel-title m-0">System Status</h3>
            </div>
            <div className="space-y-4">
              <div className="flex justify-between items-center text-sm">
                <span className="text-slate-400">Inference Engine</span>
                <span className="text-emerald-400 font-medium bg-emerald-400/10 px-2 py-0.5 rounded border border-emerald-400/20">Edge Optimized</span>
              </div>

              {results?.metadata && (
                <div className="flex justify-between items-center text-sm">
                  <span className="text-slate-400">Inference Time</span>
                  <span className="text-slate-200">{results.metadata.inference_time_ms} ms</span>
                </div>
              )}

              {controlAction?.reanalysis_performed && (
                <div className="mt-4 p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg text-sm text-blue-200">
                  <span className="block font-semibold text-blue-400 mb-1 flex items-center gap-1.5 border-b border-blue-500/20 pb-1.5 relative">
                    <span className="animate-spin mr-1 absolute -left-6 bottom-0 size-3 rounded-full border-blue-500 border-2 border-r-transparent"></span>
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
          heatmapData={results?.visualizations?.heatmap_data || []}
          boundingBoxes={results?.visualizations?.bounding_boxes || []}
          isProcessing={isProcessing}
        />

      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Uncertainty Estimates Panel */}
        <div className="lg:col-span-1">
          <UncertaintyPanel results={results} />
        </div>

        {/* Diagnostic Summary Panel & Report Generation Action */}
        <div className="panel lg:col-span-2 flex flex-col">
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
                  The deep learning ensemble has processed the supplied scan.
                  Based on inference, <strong className={results.prediction.has_tumor ? "text-red-400" : "text-emerald-400"}>
                    {results.prediction.has_tumor ? "an anomalous lesion was detected" : "no significant anomalies were detected"}.
                  </strong>
                </p>
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mt-4">
                  <div className="bg-slate-900 border border-slate-800 p-3 rounded-lg">
                    <span className="block text-xs text-slate-500 mb-1">Tumor Probability</span>
                    <span className="text-lg font-bold text-slate-200">{results.prediction.tumor_probability}%</span>
                  </div>
                  <div className="bg-slate-900 border border-slate-800 p-3 rounded-lg">
                    <span className="block text-xs text-slate-500 mb-1">Confidence</span>
                    <span className="text-lg font-bold text-slate-200">{results.prediction.confidence_score}%</span>
                  </div>
                  <div className="bg-slate-900 border border-slate-800 p-3 rounded-lg">
                    <span className="block text-xs text-slate-500 mb-1">Total Uncertainty</span>
                    <span className="text-lg font-bold text-slate-200">{results.uncertainty.total}%</span>
                  </div>
                  <div className="bg-slate-900 border border-slate-800 p-3 rounded-lg">
                    <span className="block text-xs text-slate-500 mb-1">Calibration Node</span>
                    <span className="text-lg font-bold text-slate-200 flex items-center gap-2">
                      {results.metadata.calibrated ? (
                        <><CheckCircle size={16} className="text-emerald-500" /> Active</>
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
      </div>
    </DashboardLayout>
  );
}
