'use client';

import React, { useRef, useEffect, useCallback } from 'react';
import { Eye, Focus } from 'lucide-react';

interface HeatmapPoint {
  x: number;
  y: number;
  value: number;
}

interface VisualizationPanelProps {
  originalImageSrc: string | null;
  heatmapData: HeatmapPoint[];
  boundingBoxes: number[][]; // [x, y, w, h, confidence]
  isProcessing: boolean;
}

export function VisualizationPanel({
  originalImageSrc,
  heatmapData,
  boundingBoxes,
  isProcessing,
}: VisualizationPanelProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const drawVisualization = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const W = canvas.width;
    const H = canvas.height;

    const drawOverlay = () => {
      // 1. Heatmap
      if (heatmapData && heatmapData.length > 0) {
        for (const pt of heatmapData) {
          const x = pt.x * W;
          const y = pt.y * H;
          // Scale radius by value
          const r = Math.max(10, pt.value * 25);

          const grad = ctx.createRadialGradient(x, y, 0, x, y, r);
          grad.addColorStop(0, `rgba(239, 68, 68, ${Math.min(0.8, pt.value)})`); // Red center
          grad.addColorStop(1, 'rgba(239, 68, 68, 0)'); // Transparent edge
          
          ctx.fillStyle = grad;
          ctx.beginPath();
          ctx.arc(x, y, r, 0, Math.PI * 2);
          ctx.fill();
        }
      }

      // 2. Bounding Boxes
      if (boundingBoxes && boundingBoxes.length > 0) {
        ctx.strokeStyle = '#f87171'; // Red
        ctx.lineWidth = 3;
        
        for (const box of boundingBoxes) {
          const bx = box[0] * W;
          const by = box[1] * H;
          const bw = box[2] * W;
          const bh = box[3] * H;
          const conf = box[4];

          // Draw Box
          ctx.strokeRect(bx, by, bw, bh);

          // Draw Label
          if (conf !== undefined) {
            ctx.fillStyle = '#f87171';
            ctx.font = 'bold 12px sans-serif';
            const text = `${(conf * 100).toFixed(1)}%`;
            const textWidth = ctx.measureText(text).width;
            
            // Background for text
            ctx.fillRect(bx, by - 20, textWidth + 8, 20);
            
            // Text itself
            ctx.fillStyle = '#ffffff';
            ctx.fillText(text, bx + 4, by - 5);
          }
        }
      }
    };

    if (originalImageSrc) {
      const img = new Image();
      img.src = originalImageSrc;
      img.onload = () => {
        // Draw image covering the canvas
        ctx.drawImage(img, 0, 0, W, H);
        if (!isProcessing) {
          drawOverlay();
        }
      };
    } else {
      // Empty state
      ctx.fillStyle = '#0f172a';
      ctx.fillRect(0, 0, W, H);
      
      ctx.fillStyle = '#334155';
      ctx.font = '14px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('Scan visualization will appear here', W / 2, H / 2);
    }
  }, [originalImageSrc, heatmapData, boundingBoxes, isProcessing]);

  useEffect(() => {
    drawVisualization();
  }, [drawVisualization]);

  return (
    <div className="panel lg:col-span-1 flex flex-col">
      <div className="panel-header">
        <Eye className="text-blue-400" size={20} />
        <h3 className="panel-title m-0">Scan Visualization</h3>
      </div>
      
      <div className="flex-1 relative bg-slate-950 rounded-lg overflow-hidden border border-slate-800">
        <canvas
          ref={canvasRef}
          width={512}
          height={512}
          className={`w-full h-auto aspect-square object-cover transition-opacity duration-300 ${isProcessing ? 'opacity-50 blur-sm' : 'opacity-100'}`}
        />
        
        {isProcessing && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="flex flex-col items-center gap-3 bg-slate-900/80 p-4 rounded-xl border border-slate-700 backdrop-blur-md">
              <Focus className="text-violet-400 animate-spin" size={32} />
              <span className="text-slate-200 text-sm font-medium">Extracting Features...</span>
            </div>
          </div>
        )}
      </div>

      <div className="mt-3 flex items-center justify-between text-[10px] text-slate-500">
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-red-500 opacity-80" />
          <span>High Uncertainty / Activation</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 border-2 border-red-400 rounded-sm" />
          <span>Detected Region</span>
        </div>
      </div>
    </div>
  );
}
