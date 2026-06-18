"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, Map, Zap, BarChart3,
  Bell, Search, Shield, Activity,
  ChevronDown, Cpu
} from "lucide-react";

const NAV_ITEMS = [
  { href: "/", icon: LayoutDashboard, label: "Overview", desc: "Command Center" },
  { href: "/map", icon: Map, label: "Live Map", desc: "Geospatial Intel" },
  { href: "/predictions", icon: Zap, label: "AI Predictor", desc: "Impact Simulation", badge: "AI" },
  { href: "/leaderboard", icon: Shield, label: "Leaderboard", desc: "Station Efficiency" },
  { href: "/analytics", icon: BarChart3, label: "Analytics", desc: "Telemetry Data" },
];

export function AppSidebar() {
  const pathname = usePathname();

  return (
    <aside className="glass-sidebar w-[260px] flex-shrink-0 flex flex-col h-full z-20">
      {/* Logo */}
      <div className="h-20 flex items-center px-6 border-b border-white/[0.06]">
        <div className="flex items-center gap-3.5">
          
          {/* ATC / Radar Style Logo */}
          <div className="relative w-12 h-12 rounded-[14px] bg-slate-900/50 border border-cyan-500/20 flex items-center justify-center shadow-[0_0_20px_rgba(6,182,212,0.15)] overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/10 to-blue-600/10"></div>
            <svg viewBox="0 0 24 24" fill="none" className="w-7 h-7 relative z-10">
              <circle cx="12" cy="12" r="8" stroke="#06B6D4" strokeWidth="1.5" strokeDasharray="3 3" opacity="0.6"/>
              <circle cx="12" cy="12" r="4" stroke="#3B82F6" strokeWidth="2"/>
              <circle cx="12" cy="12" r="1" fill="#fff" />
              <path d="M12 2v3M12 19v3M2 12h3M19 12h3" stroke="#06B6D4" strokeWidth="1.5" strokeLinecap="round" opacity="0.8"/>
            </svg>
          </div>

          <div className="flex flex-col justify-center mt-0.5">
            <h1 className="text-[20px] text-white leading-none tracking-tight flex items-center">
              <span className="font-bold">EventFlow</span>
              <span className="font-light text-cyan-400 ml-1">AI</span>
            </h1>
            <p className="text-[9.5px] text-slate-400 font-bold mt-1.5 tracking-[0.2em] uppercase">
              Traffic Intelligence
            </p>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
        <p className="section-label px-2 mb-3">Navigation</p>

        {NAV_ITEMS.map(({ href, icon: Icon, label, desc, badge }) => {
          const active = pathname === href;
          return (
            <Link key={href} href={href}>
              <div className={`nav-item ${active ? "active" : ""}`}>
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center transition-all ${active
                    ? "bg-blue-500/20 text-blue-400"
                    : "bg-white/[0.04] text-slate-500 group-hover:text-slate-300"
                  }`}>
                  <Icon size={16} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className={`text-[13px] font-medium leading-none ${active ? "text-blue-300" : "text-slate-300"}`}>{label}</p>
                  <p className="text-[11px] text-slate-600 mt-0.5 leading-none">{desc}</p>
                </div>
                {badge && (
                  <span className="badge badge-blue text-[10px]">{badge}</span>
                )}
              </div>
            </Link>
          );
        })}

        <div className="pt-4 mt-2 border-t border-white/[0.05]">
          <p className="section-label px-2 mb-3">System</p>
          <div className="nav-item">
            <div className="w-8 h-8 rounded-lg bg-white/[0.04] flex items-center justify-center">
              <Cpu size={16} className="text-slate-500" />
            </div>
            <div className="flex-1">
              <p className="text-[13px] font-medium text-slate-300">ML Engine</p>
              <p className="text-[11px] text-slate-600 mt-0.5">XGBoost + LightGBM</p>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="status-dot bg-emerald-400" style={{ color: "rgba(52,211,153,0.5)" }}></div>
              <span className="text-[10px] text-emerald-400 font-medium">Live</span>
            </div>
          </div>
        </div>
      </nav>

      {/* User */}
      <div className="p-3 border-t border-white/[0.06]">
        <div className="flex items-center gap-3 p-2 rounded-xl hover:bg-white/[0.04] cursor-pointer transition-all group">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-600 to-purple-600 flex items-center justify-center text-white text-sm font-bold shadow-lg">
            BT
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-[13px] font-semibold text-slate-200 leading-none">Bengaluru TMC</p>
            <p className="text-[11px] text-slate-500 mt-0.5">Traffic Control Unit</p>
          </div>
          <ChevronDown size={14} className="text-slate-600 group-hover:text-slate-400 transition-colors" />
        </div>
      </div>
    </aside>
  );
}
