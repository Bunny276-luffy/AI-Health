'use client';

import React from 'react';
import { Sidebar } from './Sidebar';

export function DashboardLayout({ children }: { children: React.ReactNode }) {
    return (
        <div className="flex h-screen overflow-hidden bg-slate-950">
            <Sidebar />
            <main className="flex-1 flex flex-col overflow-hidden relative">
                <header className="h-16 border-b border-slate-800 bg-slate-900/50 backdrop-blur-md flex items-center justify-between px-6 shrink-0 z-10">
                    <h1 className="text-lg font-semibold text-slate-200">Clinical Diagnosis</h1>
                    <div className="flex items-center gap-3">
                        <span className="text-sm font-medium text-slate-300">Dr. Smith, M.D.</span>
                        <img
                            src="https://ui-avatars.com/api/?name=Dr+Smith&background=0D8ABC&color=fff"
                            alt="User"
                            className="w-8 h-8 rounded-full border border-slate-700"
                        />
                    </div>
                </header>

                <div className="flex-1 overflow-y-auto p-4 md:p-6 lg:p-8 custom-scrollbar">
                    <div className="max-w-[1600px] w-full mx-auto space-y-6">
                        {children}
                    </div>
                </div>
            </main>
        </div>
    );
}
