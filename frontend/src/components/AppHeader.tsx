"use client";

import { Bell, Search, Shield, Clock } from "lucide-react";
import { useState, useEffect } from "react";

export function AppHeader() {
  const [time, setTime] = useState("");

  useEffect(() => {
    const update = () => {
      const now = new Date();
      setTime(now.toLocaleTimeString("en-IN", {
        hour: "2-digit", minute: "2-digit", second: "2-digit",
        hour12: false, timeZone: "Asia/Kolkata"
      }));
    };
    update();
    const id = setInterval(update, 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <header className="glass-header h-14 flex items-center justify-between px-6 flex-shrink-0">
      {/* Search */}
      <div className="flex items-center gap-3">
        <div className="relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            placeholder="Search incidents, zones, routes..."
            className="w-72 h-9 pl-9 pr-4 bg-white/[0.04] border border-white/[0.07] rounded-lg text-[13px] text-slate-300 placeholder-slate-600 outline-none focus:border-blue-500/40 focus:bg-blue-500/[0.03] transition-all"
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                alert(`Searching for: ${e.currentTarget.value}\n\nSearch functionality is mocked for this demo.`);
              }
            }}
          />
        </div>
      </div>

      {/* Right Side */}
      <div className="flex items-center gap-3">
        {/* Live Clock */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/[0.03] border border-white/[0.06]">
          <Clock size={12} className="text-slate-500" />
          <span className="mono text-[12px] text-slate-400">{time}</span>
          <span className="text-[10px] text-slate-600">IST</span>
        </div>

        {/* AI Status */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-500/[0.08] border border-emerald-500/20">
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></div>
          <span className="text-[12px] text-emerald-400 font-medium">AI Models Active</span>
        </div>

        {/* Notifications */}
        <button className="relative w-9 h-9 rounded-lg bg-white/[0.04] border border-white/[0.08] flex items-center justify-center text-slate-400 hover:text-slate-200 hover:bg-white/[0.07] transition-all">
          <Bell size={15} />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full border border-[#050816]"></span>
        </button>

        {/* Divider */}
        <div className="w-px h-6 bg-white/[0.08]"></div>

        {/* Org Badge */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/[0.03] border border-white/[0.06]">
          <Shield size={13} className="text-blue-400" />
          <span className="text-[12px] font-medium text-slate-300">BLR Traffic Dept</span>
        </div>
      </div>
    </header>
  );
}
