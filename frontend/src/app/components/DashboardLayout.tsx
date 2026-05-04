'use client';

import React, { ReactNode } from 'react';
import { Activity, Brain, Shield } from 'lucide-react';

interface DashboardLayoutProps {
  children: ReactNode;
}

export function DashboardLayout({ children }: DashboardLayoutProps) {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-50">
      {/* Top Navigation Bar */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-screen-2xl mx-auto px-6 py-3 flex items-center justify-between">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="relative flex items-center justify-center w-9 h-9 bg-violet-600/20 border border-violet-500/30 rounded-lg">
              <Brain size={20} className="text-violet-400" />
              <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-emerald-400 rounded-full border-2 border-slate-900 animate-pulse" />
            </div>
            <div>
              <span className="font-bold text-slate-100 text-base tracking-tight">NeuroScan</span>
              <span className="ml-2 text-[10px] font-medium bg-violet-500/20 text-violet-300 border border-violet-500/20 px-1.5 py-0.5 rounded-full align-middle">
                v2.0
              </span>
            </div>
          </div>

          {/* Nav Pills */}
          <nav className="hidden md:flex items-center gap-1">
            {['Dashboard', 'Scan Analysis', 'Reports'].map((item) => (
              <button
                key={item}
                className="px-3 py-1.5 text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-colors"
              >
                {item}
              </button>
            ))}
          </nav>

          {/* Status Indicators */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 text-xs text-emerald-400 bg-emerald-400/10 border border-emerald-400/20 px-2.5 py-1 rounded-full">
              <Activity size={11} className="animate-pulse" />
              <span>API Online</span>
            </div>
            <div className="flex items-center gap-1.5 text-xs text-violet-400 bg-violet-400/10 border border-violet-400/20 px-2.5 py-1 rounded-full">
              <Shield size={11} />
              <span>90% Conformal</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-screen-2xl mx-auto px-6 py-6 space-y-6">
        {children}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 mt-12 py-4 text-center text-xs text-slate-600">
        NeuroScan v2.0 — AI-assisted screening tool only. Not a substitute for clinical diagnosis.
      </footer>
    </div>
  );
}
