'use client';

import React, { useState } from 'react';
import { Maximize2, Layers } from 'lucide-react';
import clsx from 'clsx';

interface VizProps {
    originalImageSrc: string | null;
    heatmapData: { x: number; y: number; value: number }[];
    boundingBoxes: number[][]; // [x, y, w, h, conf]
    isProcessing: boolean;
}

export function VisualizationPanel({ originalImageSrc, heatmapData, boundingBoxes, isProcessing }: VizProps) {
    const [activeLayer, setActiveLayer] = useState<'heatmap' | 'bbox' | 'both' | 'none'>('both');

    const renderDots = () => {
        if (activeLayer === 'none' || activeLayer === 'bbox') return null;
        return heatmapData.map((pt, i) => (
            <div
                key={i}
                className="tumor-dot"
                style={{
                    left: `calc(${pt.x * 100}% - 3px)`,
                    top: `calc(${pt.y * 100}% - 3px)`,
                    width: '6px',
                    height: '6px',
                    backgroundColor: `hsl(${Math.max(0, 120 - pt.value * 120)}, 100%, 50%)`,
                    boxShadow: `0 0 8px hsl(${Math.max(0, 120 - pt.value * 120)}, 100%, 50%)`,
                    animationDelay: `${Math.random() * 2}s`
                }}
            />
        ));
    };

    const renderBBoxes = () => {
        if (activeLayer === 'none' || activeLayer === 'heatmap') return null;
        return boundingBoxes.map((box, i) => {
            const [x, y, w, h, conf] = box;
            return (
                <div
                    key={`bbox-${i}`}
                    className="absolute border-2 border-red-500 z-10 pointers-events-none"
                    style={{
                        left: `${x * 100}%`,
                        top: `${y * 100}%`,
                        width: `${w * 100}%`,
                        height: `${h * 100}%`,
                        boxShadow: '0 0 15px rgba(239, 68, 68, 0.5), inset 0 0 15px rgba(239, 68, 68, 0.2)'
                    }}
                >
                    <div className="absolute -top-6 -left-0.5 bg-red-500 text-white text-[10px] font-bold px-1.5 py-0.5 shadow-md">
                        Tumor: {Math.round(conf * 100)}%
                    </div>
                </div>
            );
        });
    };

    return (
        <div className="panel lg:col-span-2 flex flex-col min-h-[500px]">
            <div className="panel-header justify-between">
                <div className="flex items-center gap-2">
                    <Layers className="text-blue-500" size={20} />
                    <h3 className="panel-title m-0">Diagnostic Visualization</h3>
                </div>

                <div className="flex gap-2 bg-slate-950 p-1 rounded-lg border border-slate-800">
                    {['both', 'heatmap', 'bbox', 'none'].map(layer => (
                        <button
                            key={layer}
                            onClick={() => setActiveLayer(layer as any)}
                            className={clsx(
                                "px-3 py-1 text-xs font-medium rounded-md capitalize transition-colors",
                                activeLayer === layer ? "bg-slate-800 text-slate-100" : "text-slate-500 hover:text-slate-300"
                            )}
                        >
                            {layer}
                        </button>
                    ))}
                </div>
            </div>

            <div className="flex-1 bg-black rounded-xl border border-slate-800 relative flex items-center justify-center overflow-hidden group">
                {!originalImageSrc ? (
                    <div className="text-slate-600 text-sm font-medium">No scan available for analysis</div>
                ) : (
                    <div className="relative inline-block max-w-full max-h-full">
                        <img
                            src={originalImageSrc}
                            alt="Medical Scan"
                            className={clsx(
                                "max-w-full max-h-[60vh] object-contain transition-opacity duration-500",
                                isProcessing && "opacity-30 blur-sm"
                            )}
                        />

                        {/* Overlays Container */}
                        <div className="absolute inset-0 pointer-events-none overflow-hidden">
                            {renderDots()}
                            {renderBBoxes()}
                        </div>

                        {/* Simulated Edge Processing Scanner */}
                        {isProcessing && (
                            <div className="absolute inset-0 z-20 overflow-hidden pointers-events-none">
                                <div className="w-full h-1 bg-blue-500 shadow-[0_0_20px_#3b82f6] absolute top-0 animate-[scan_2s_linear_infinite_alternate]"></div>
                            </div>
                        )}

                        <button className="absolute bottom-4 right-4 bg-slate-900/80 p-2 rounded-lg text-slate-400 hover:text-white backdrop-blur-sm opacity-0 group-hover:opacity-100 transition-opacity">
                            <Maximize2 size={18} />
                        </button>
                    </div>
                )}
            </div>

            {/* Global scan animation logic using arbitrary tailwind isn't supported out of the box so adding standard class via layout or style block */}
            <style dangerouslySetInnerHTML={{
                __html: `
        @keyframes scan {
          0% { top: 0; }
          100% { top: 100%; }
        }
      `}} />
        </div>
    );
}
