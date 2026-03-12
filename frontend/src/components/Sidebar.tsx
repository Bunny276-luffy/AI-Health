'use client';

import React, { useState } from 'react';
import {
    Brain, LayoutDashboard, History, Settings, FileText, Activity
} from 'lucide-react';
import clsx from 'clsx';

export function Sidebar() {
    const [active, setActive] = useState('dashboard');

    const navItems = [
        { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
        { id: 'history', label: 'Patient History', icon: History },
        { id: 'reports', label: 'Diagnostic Reports', icon: FileText },
        { id: 'settings', label: 'Settings', icon: Settings },
    ];

    return (
        <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col h-screen shrink-0 relative z-20">
            <div className="flex items-center gap-3 p-6 border-b border-slate-800 text-blue-500">
                <Brain size={32} />
                <h2 className="text-xl font-bold text-slate-100 tracking-wide">NeuroScan AI</h2>
            </div>

            <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
                {navItems.map((item) => {
                    const Icon = item.icon;
                    const isActive = active === item.id;
                    return (
                        <button
                            key={item.id}
                            onClick={() => setActive(item.id)}
                            className={clsx(
                                "w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 text-sm font-medium",
                                isActive
                                    ? "bg-blue-500/10 text-blue-400"
                                    : "text-slate-400 hover:bg-slate-800/50 hover:text-slate-200"
                            )}
                        >
                            <Icon size={18} />
                            {item.label}
                        </button>
                    )
                })}
            </nav>

            <div className="p-4 border-t border-slate-800 space-y-4">
                <div className="flex items-center gap-3 text-sm text-slate-400">
                    <div className="relative flex h-3 w-3">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
                    </div>
                    <span>API: Edge Inference</span>
                </div>
            </div>
        </aside>
    );
}
