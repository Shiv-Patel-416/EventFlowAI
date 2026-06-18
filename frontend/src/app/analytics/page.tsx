"use client";

import { useEffect, useState } from "react";
import { analyticsService } from "@/lib/api";
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Cell, PieChart, Pie, Legend,
  AreaChart, Area
} from "recharts";
import { motion } from "framer-motion";
import { BarChart3, TrendingUp, Clock, MapPin } from "lucide-react";

const HOURLY_DATA = Array.from({ length: 24 }, (_, i) => ({
  hour: `${String(i).padStart(2, "0")}:00`,
  incidents: Math.floor(
    (i > 7 && i < 10 ? 500 : i > 17 && i < 21 ? 480 : i > 12 && i < 14 ? 250 : 80)
    + Math.random() * 60
  ),
}));

const ZONE_DATA = [
  { zone: "Silk Board",    count: 2340, color: "#EF4444" },
  { zone: "KR Puram",     count: 1820, color: "#FB923C" },
  { zone: "Hebbal",       count: 1640, color: "#FACC15" },
  { zone: "Whitefield",   count: 1290, color: "#3B82F6" },
  { zone: "Koramangala",  count: 1080, color: "#10B981" },
];

const CAUSE_DATA = [
  { name: "Vehicle Breakdown", count: 4944, fill: "#3B82F6" },
  { name: "Pot Holes",         count: 968,  fill: "#06B6D4" },
  { name: "Others",            count: 541,  fill: "#A78BFA" },
  { name: "Water Logging",     count: 421,  fill: "#FACC15" },
  { name: "Tree Fall",         count: 288,  fill: "#10B981" },
  { name: "Public Events",     count: 86,   fill: "#FB923C" },
];

const MONTHLY_TREND = [
  { month: "Jan", events: 680, closures: 52 },
  { month: "Feb", events: 740, closures: 61 },
  { month: "Mar", events: 810, closures: 70 },
  { month: "Apr", events: 760, closures: 65 },
  { month: "May", events: 890, closures: 78 },
  { month: "Jun", events: 850, closures: 72 },
  { month: "Jul", events: 920, closures: 84 },
];

const stagger = { hidden: {}, show: { transition: { staggerChildren: 0.08 } } };
const fadeUp = { hidden: { opacity: 0, y: 16 }, show: { opacity: 1, y: 0, transition: { duration: 0.4 } } };

const TOOLTIP_STYLE = {
  background: "rgba(11,16,32,0.97)",
  border: "1px solid rgba(255,255,255,0.09)",
  borderRadius: "10px",
  fontSize: "12px",
  color: "#F1F5F9",
};

export default function AnalyticsPage() {
  return (
    <div className="h-full overflow-y-auto">
      <div className="p-6 space-y-6">

        {/* Header */}
        <motion.div initial={{ opacity:0, y:-10 }} animate={{ opacity:1, y:0 }}>
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <div className="w-7 h-7 rounded-lg bg-cyan-500/20 flex items-center justify-center">
                  <BarChart3 size={14} className="text-cyan-400" />
                </div>
                <span className="badge badge-cyan">Analytics</span>
              </div>
              <h1 className="text-2xl font-bold text-white tracking-tight">Traffic Telemetry</h1>
              <p className="text-[13px] text-slate-500 mt-0.5">Historical incident analysis across Bengaluru metropolitan</p>
            </div>
            <div className="flex items-center gap-3">
              <span className="badge badge-blue">FY 2024–25</span>
              <button 
                onClick={() => alert("CSV Export initialized. Download will begin shortly.")}
                className="btn-secondary text-[13px]"
              >
                <TrendingUp size={13} /> Export CSV
              </button>
            </div>
          </div>
        </motion.div>

        {/* Top summary strip */}
        <motion.div variants={stagger} initial="hidden" animate="show" className="grid grid-cols-4 gap-4">
          {[
            { label: "Total Incidents",  value: "8,173",  sub: "All categories", color: "text-blue-400",   icon: BarChart3 },
            { label: "Peak Hour",        value: "08:30",  sub: "Morning rush",   color: "text-orange-400", icon: Clock },
            { label: "Highest Zone",     value: "Silk Board", sub: "2,340 incidents", color: "text-red-400", icon: MapPin },
            { label: "Model Accuracy",   value: "92%",    sub: "Closure pred.",  color: "text-emerald-400",icon: TrendingUp },
          ].map(({ label, value, sub, color, icon: Icon }) => (
            <motion.div key={label} variants={fadeUp} className="kpi-card">
              <div className={`w-9 h-9 rounded-xl bg-white/[0.05] flex items-center justify-center ${color} mb-3`}>
                <Icon size={16} />
              </div>
              <p className="text-slate-500 text-[11px] font-medium mb-1">{label}</p>
              <p className="text-[22px] font-bold text-white tracking-tight mono">{value}</p>
              <p className="text-[11px] text-slate-600 mt-0.5">{sub}</p>
            </motion.div>
          ))}
        </motion.div>

        {/* Charts row 1 */}
        <div className="grid grid-cols-3 gap-5">

          {/* Hourly distribution area chart */}
          <motion.div initial={{ opacity:0, y:16 }} animate={{ opacity:1, y:0 }} transition={{ delay:0.2 }} className="col-span-2 glass-card p-5">
            <div className="flex items-center justify-between mb-5">
              <div>
                <h3 className="text-[14px] font-semibold text-white">Incidents by Hour of Day</h3>
                <p className="text-[12px] text-slate-500 mt-0.5">24-hour traffic pattern analysis</p>
              </div>
              <span className="badge badge-cyan">Avg. daily</span>
            </div>
            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={HOURLY_DATA} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%"   stopColor="#3B82F6" stopOpacity={0.3} />
                      <stop offset="100%" stopColor="#3B82F6" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
                  <XAxis
                    dataKey="hour"
                    axisLine={false} tickLine={false}
                    tick={{ fill: "#475569", fontSize: 10 }}
                    interval={3}
                  />
                  <YAxis axisLine={false} tickLine={false} tick={{ fill: "#475569", fontSize: 10 }} />
                  <Tooltip contentStyle={TOOLTIP_STYLE} cursor={{ stroke: "rgba(59,130,246,0.2)" }} />
                  <Area type="monotone" dataKey="incidents" stroke="#3B82F6" strokeWidth={2} fill="url(#areaGrad)" dot={false} activeDot={{ r: 5, fill: "#3B82F6", strokeWidth: 0 }} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </motion.div>

          {/* Zone distribution donut */}
          <motion.div initial={{ opacity:0, y:16 }} animate={{ opacity:1, y:0 }} transition={{ delay:0.25 }} className="glass-card p-5">
            <h3 className="text-[14px] font-semibold text-white mb-1">Incidents by Zone</h3>
            <p className="text-[12px] text-slate-500 mb-4">Top 5 congestion hotspots</p>
            <div className="h-40">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={ZONE_DATA} cx="50%" cy="50%" innerRadius={45} outerRadius={68} paddingAngle={4} dataKey="count" stroke="none">
                    {ZONE_DATA.map((z, i) => <Cell key={i} fill={z.color} />)}
                  </Pie>
                  <Tooltip contentStyle={TOOLTIP_STYLE} />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="space-y-2 mt-2">
              {ZONE_DATA.map(z => (
                <div key={z.zone} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: z.color }}></div>
                    <span className="text-[11px] text-slate-400">{z.zone}</span>
                  </div>
                  <span className="mono text-[11px] text-slate-500">{z.count.toLocaleString()}</span>
                </div>
              ))}
            </div>
          </motion.div>
        </div>

        {/* Charts row 2 */}
        <div className="grid grid-cols-2 gap-5">

          {/* Monthly trend */}
          <motion.div initial={{ opacity:0, y:16 }} animate={{ opacity:1, y:0 }} transition={{ delay:0.3 }} className="glass-card p-5">
            <div className="flex items-center justify-between mb-5">
              <div>
                <h3 className="text-[14px] font-semibold text-white">Monthly Incident Trend</h3>
                <p className="text-[12px] text-slate-500 mt-0.5">Events vs Road Closures</p>
              </div>
            </div>
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={MONTHLY_TREND} margin={{ top: 0, right: 0, left: -20, bottom: 0 }} barGap={4} barSize={14}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
                  <XAxis dataKey="month" axisLine={false} tickLine={false} tick={{ fill: "#475569", fontSize: 11 }} />
                  <YAxis axisLine={false} tickLine={false} tick={{ fill: "#475569", fontSize: 11 }} />
                  <Tooltip contentStyle={TOOLTIP_STYLE} />
                  <Bar dataKey="events"   fill="#3B82F6" radius={[4, 4, 0, 0]} fillOpacity={0.8} name="Incidents" />
                  <Bar dataKey="closures" fill="#EF4444" radius={[4, 4, 0, 0]} fillOpacity={0.8} name="Closures" />
                  <Legend wrapperStyle={{ fontSize: "11px", color: "#64748B", paddingTop: "8px" }} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </motion.div>

          {/* Cause breakdown */}
          <motion.div initial={{ opacity:0, y:16 }} animate={{ opacity:1, y:0 }} transition={{ delay:0.35 }} className="glass-card p-5">
            <div className="flex items-center justify-between mb-5">
              <div>
                <h3 className="text-[14px] font-semibold text-white">Cause Distribution</h3>
                <p className="text-[12px] text-slate-500 mt-0.5">Breakdown of 8,173 incidents</p>
              </div>
            </div>
            <div className="space-y-3">
              {CAUSE_DATA.map((c) => (
                <div key={c.name}>
                  <div className="flex justify-between mb-1">
                    <span className="text-[12px] text-slate-400">{c.name}</span>
                    <span className="mono text-[12px] text-slate-500">{c.count.toLocaleString()}</span>
                  </div>
                  <div className="h-1.5 rounded-full bg-white/[0.06] overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${(c.count / 4944) * 100}%` }}
                      transition={{ duration: 0.8, delay: 0.4, ease: "easeOut" }}
                      className="h-full rounded-full"
                      style={{ background: c.fill }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        </div>

      </div>
    </div>
  );
}
