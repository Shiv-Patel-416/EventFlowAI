"use client";

import { useState, useEffect, useRef } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import {
  Activity, AlertTriangle, MapPin, TrendingUp,
  Clock, CheckCircle2, Zap, Navigation2, BarChart3,
} from "lucide-react";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer,
} from "recharts";
import { eventService } from "@/lib/api";

/* ── Hourly traffic data ─────────────────────────────────────── */
const HOURLY = Array.from({ length: 24 }, (_, i) => ({
  hour: `${String(i).padStart(2, "0")}:00`,
  incidents: Math.floor(
    (i > 7 && i < 10 ? 480 : i > 17 && i < 21 ? 460 : i > 12 && i < 14 ? 220 : 60)
    + Math.random() * 50
  ),
}));

/* ── Recent incidents (live feed) ────────────────────────────── */
const FEED = [
  { id: 1, zone: "Silk Board Junction",    cause: "Water Logging",     sev: "critical", time: "2m ago",  delay: 38 },
  { id: 2, zone: "Whitefield Main Road",   cause: "Accident",          sev: "high",     time: "6m ago",  delay: 24 },
  { id: 3, zone: "MG Road Junction",       cause: "Public Event",      sev: "high",     time: "11m ago", delay: 18 },
  { id: 4, zone: "Koramangala 6th Block",  cause: "Vehicle Breakdown", sev: "medium",   time: "18m ago", delay: 12 },
  { id: 5, zone: "Indiranagar 100ft Rd",  cause: "VIP Movement",      sev: "medium",   time: "25m ago", delay: 9  },
  { id: 6, zone: "Hebbal Flyover",         cause: "Tree Fall",         sev: "medium",   time: "31m ago", delay: 11 },
  { id: 7, zone: "KR Puram Bridge",        cause: "Pot Holes",         sev: "low",      time: "45m ago", delay: 5  },
];

const SEV_BADGE: Record<string, string> = {
  critical: "badge-red",
  high:     "badge-orange",
  medium:   "badge-yellow",
  low:      "badge-green",
};

const CAUSE_BREAKDOWN = [
  { name: "Vehicle Breakdown", pct: 60, color: "#3B82F6" },
  { name: "Pot Holes",         pct: 12, color: "#06B6D4" },
  { name: "Water Logging",     pct: 8,  color: "#FACC15" },
  { name: "Tree Fall",         pct: 5,  color: "#10B981" },
  { name: "Public Events",     pct: 3,  color: "#FB923C" },
  { name: "Others",            pct: 12, color: "#A78BFA" },
];

/* ── CountUp animation ───────────────────────────────────────── */
function CountUp({ target, suffix = "" }: { target: number; suffix?: string }) {
  const [val, setVal] = useState(0);
  useEffect(() => {
    let start = 0;
    const step = target / 60;
    const iv = setInterval(() => {
      start += step;
      if (start >= target) { setVal(target); clearInterval(iv); }
      else setVal(Math.floor(start));
    }, 16);
    return () => clearInterval(iv);
  }, [target]);
  return <>{val.toLocaleString()}{suffix}</>;
}

const TOOLTIP_STYLE = {
  background: "rgba(11,16,32,0.97)",
  border: "1px solid rgba(255,255,255,0.09)",
  borderRadius: "10px",
  fontSize: "12px",
  color: "#F1F5F9",
};

const stagger = { hidden: {}, show: { transition: { staggerChildren: 0.07 } } };
const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  show:   { opacity: 1, y: 0, transition: { duration: 0.4, ease: "easeOut" as const } },
};

export default function DashboardPage() {
  const [stats, setStats] = useState({
    total_incidents: 8173,
    active_incidents: 9,
    high_priority: 2,
    avg_delay_minutes: 17,
    model_accuracy: 92,
    road_closures: 2,
  });

  useEffect(() => {
    eventService.getDashboardStats()
      .then(d => {
        if (!d) return;
        // Backend returns different field names — map them
        setStats({
          total_incidents:  d.total_events        ?? d.total_incidents  ?? 8173,
          active_incidents: d.active_events        ?? d.active_incidents ?? 9,
          high_priority:    d.event_related_incidents ?? 2,
          avg_delay_minutes: 17,
          model_accuracy:   d.model_accuracy?.closure_accuracy
                              ? Math.round(d.model_accuracy.closure_accuracy * 100)
                              : 92,
          road_closures:    d.road_closures ?? 2,
        });
      })
      .catch(() => {/* use defaults */});
  }, []);

  const KPI_CARDS = [
    { label: "Active Incidents",   value: stats.active_incidents,  suffix: "",  color: "text-red-400",     icon: AlertTriangle, badge: "badge-red",    desc: "Across monitored corridors" },
    { label: "Critical / High",    value: stats.high_priority,     suffix: "",  color: "text-orange-400",  icon: Zap,           badge: "badge-orange", desc: "Requiring immediate action"  },
    { label: "Avg Delay",          value: stats.avg_delay_minutes, suffix: "m", color: "text-yellow-400",  icon: Clock,         badge: "badge-yellow", desc: "Per affected corridor"       },
    { label: "Model Accuracy",     value: stats.model_accuracy,    suffix: "%", color: "text-emerald-400", icon: TrendingUp,    badge: "badge-green",  desc: "Road closure prediction"     },
  ];

  return (
    <div className="h-full overflow-y-auto">
      <div className="p-6 space-y-6">

        {/* ── Header ───────────────────────────────────────────── */}
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <div className="w-2 h-2 rounded-full bg-emerald-400 animate-glow-pulse" />
                <span className="badge badge-green">Live Feed</span>
              </div>
              <h1 className="text-2xl font-bold text-white tracking-tight">City Command Center</h1>
              <p className="text-[13px] text-slate-500 mt-0.5">Bengaluru metropolitan real-time incident intelligence</p>
            </div>
            <div className="flex items-center gap-3">
              <span className="badge badge-blue">IST {new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" })}</span>
              <Link href="/analytics" className="btn-secondary text-[13px] no-underline">
                <BarChart3 size={13} /> Analytics
              </Link>
            </div>
          </div>
        </motion.div>

        {/* ── KPI Row ───────────────────────────────────────────── */}
        <motion.div variants={stagger} initial="hidden" animate="show" className="grid grid-cols-4 gap-4">
          {KPI_CARDS.map(({ label, value, suffix, color, icon: Icon, badge, desc }) => (
            <motion.div key={label} variants={fadeUp} className="kpi-card">
              <div className="flex items-center justify-between mb-4">
                <div className={`w-9 h-9 rounded-xl bg-white/[0.05] flex items-center justify-center ${color}`}>
                  <Icon size={16} />
                </div>
                <span className={`badge ${badge}`}>{label}</span>
              </div>
              <p className="mono text-[28px] font-bold text-white tracking-tight leading-none mb-1">
                <CountUp target={value} suffix={suffix} />
              </p>
              <p className="text-[11px] text-slate-600 mt-2">{desc}</p>
            </motion.div>
          ))}
        </motion.div>

        {/* ── Charts + Feed ──────────────────────────────────────── */}
        <div className="grid grid-cols-12 gap-5">

          {/* Hourly traffic area chart */}
          <motion.div
            initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
            className="col-span-8 glass-card p-5"
          >
            <div className="flex items-center justify-between mb-5">
              <div>
                <h3 className="text-[14px] font-semibold text-white">Traffic Incident Density</h3>
                <p className="text-[12px] text-slate-500 mt-0.5">Hourly distribution — 24h pattern</p>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-blue-400" />
                <span className="text-[11px] text-slate-500">Incidents</span>
              </div>
            </div>
            <div className="h-52">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={HOURLY} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="aGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%"   stopColor="#3B82F6" stopOpacity={0.35} />
                      <stop offset="100%" stopColor="#3B82F6" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
                  <XAxis dataKey="hour" axisLine={false} tickLine={false} tick={{ fill: "#475569", fontSize: 10 }} interval={3} />
                  <YAxis axisLine={false} tickLine={false} tick={{ fill: "#475569", fontSize: 10 }} />
                  <Tooltip contentStyle={TOOLTIP_STYLE} cursor={{ stroke: "rgba(59,130,246,0.2)" }} />
                  <Area type="monotone" dataKey="incidents" stroke="#3B82F6" strokeWidth={2} fill="url(#aGrad)" dot={false} activeDot={{ r: 5, fill: "#3B82F6", strokeWidth: 0 }} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </motion.div>

          {/* Cause breakdown */}
          <motion.div
            initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25 }}
            className="col-span-4 glass-card p-5"
          >
            <h3 className="text-[14px] font-semibold text-white mb-1">Cause Breakdown</h3>
            <p className="text-[12px] text-slate-500 mb-4">8,173 incidents — Bengaluru Astram dataset</p>
            <div className="space-y-3">
              {CAUSE_BREAKDOWN.map(c => (
                <div key={c.name}>
                  <div className="flex justify-between mb-1">
                    <span className="text-[11px] text-slate-400">{c.name}</span>
                    <span className="mono text-[11px] text-slate-500">{c.pct}%</span>
                  </div>
                  <div className="h-1.5 rounded-full bg-white/[0.06] overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${c.pct}%` }}
                      transition={{ duration: 0.7, delay: 0.3, ease: "easeOut" }}
                      className="h-full rounded-full"
                      style={{ background: c.color }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        </div>

        {/* ── Live Incident Feed ────────────────────────────────── */}
        <motion.div
          initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}
          className="glass-card p-5"
        >
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-3">
              <h3 className="text-[14px] font-semibold text-white">Live Incident Feed</h3>
              <span className="badge badge-red">
                <span className="w-1.5 h-1.5 rounded-full bg-red-400 animate-glow-pulse" />
                {stats.active_incidents} Active
              </span>
            </div>
            <button className="btn-ghost text-[12px]">View All →</button>
          </div>

          <div className="grid grid-cols-7 gap-3 text-[10px] text-slate-600 uppercase tracking-wider mb-2 px-1">
            <span className="col-span-2">Location</span>
            <span className="col-span-2">Cause</span>
            <span>Severity</span>
            <span>Delay</span>
            <span>Time</span>
          </div>

          <div className="space-y-1.5">
            {FEED.map((inc, i) => (
              <motion.div
                key={inc.id}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.35 + i * 0.04 }}
                className="grid grid-cols-7 gap-3 items-center px-3 py-3 rounded-xl hover:bg-white/[0.03] transition-colors border border-transparent hover:border-white/[0.06] cursor-default group"
              >
                {/* Color severity strip */}
                <div className="col-span-2 flex items-center gap-2.5">
                  <div className={`w-1 h-8 rounded-full flex-shrink-0 ${
                    inc.sev === "critical" ? "bg-red-500" :
                    inc.sev === "high"     ? "bg-orange-400" :
                    inc.sev === "medium"   ? "bg-yellow-400" : "bg-emerald-400"
                  }`} />
                  <div>
                    <p className="text-[12px] font-medium text-slate-200 leading-tight">{inc.zone}</p>
                  </div>
                </div>
                <span className="col-span-2 text-[12px] text-slate-400">{inc.cause}</span>
                <span><span className={`badge ${SEV_BADGE[inc.sev]} capitalize`}>{inc.sev}</span></span>
                <span className={`mono text-[13px] font-semibold ${inc.delay > 20 ? "text-red-400" : inc.delay > 10 ? "text-yellow-400" : "text-emerald-400"}`}>
                  +{inc.delay}m
                </span>
                <span className="text-[11px] text-slate-600">{inc.time}</span>
              </motion.div>
            ))}
          </div>
        </motion.div>

      </div>
    </div>
  );
}
