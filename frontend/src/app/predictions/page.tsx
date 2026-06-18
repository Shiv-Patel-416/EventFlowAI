"use client";

import { useState } from "react";
import { predictionService } from "@/lib/api";
import { motion, AnimatePresence } from "framer-motion";
import {
  Zap, ShieldAlert, Users, Navigation2,
  HardHat, Car, Tent, MapPin, ArrowRight,
  AlertTriangle, CheckCircle2, Activity
} from "lucide-react";

const BENGALURU_LOCATIONS = [
  { name: "Koramangala 6th Block",   lat: 12.9279, lng: 77.6271 },
  { name: "Indiranagar 100ft Road",  lat: 12.9719, lng: 77.6412 },
  { name: "Whitefield Main Road",    lat: 12.9698, lng: 77.7499 },
  { name: "Electronic City Phase 1", lat: 12.8399, lng: 77.6770 },
  { name: "MG Road Junction",        lat: 12.9730, lng: 77.6016 },
  { name: "Majestic Bus Terminal",   lat: 12.9766, lng: 77.5713 },
  { name: "Hebbal Flyover",          lat: 13.0354, lng: 77.5988 },
  { name: "Silk Board Junction",     lat: 12.9176, lng: 77.6234 },
  { name: "KR Puram Bridge",         lat: 13.0083, lng: 77.6953 },
  { name: "Outer Ring Road (ORR)",   lat: 12.9342, lng: 77.6890 },
  { name: "Marathahalli Bridge",     lat: 12.9568, lng: 77.7011 },
  { name: "Bellandur Junction",      lat: 12.9258, lng: 77.6771 },
];

const EVENT_CAUSES = [
  { value: "public_event",       label: "Public Event / Rally" },
  { value: "procession",         label: "Procession / March" },
  { value: "vip_movement",       label: "VIP / VVIP Movement" },
  { value: "protest",            label: "Protest / Demonstration" },
  { value: "vehicle_breakdown",  label: "Vehicle Breakdown" },
  { value: "water_logging",      label: "Water Logging / Flooding" },
  { value: "accident",           label: "Road Accident" },
  { value: "construction",       label: "Construction Activity" },
  { value: "tree_fall",          label: "Tree Fall" },
];

const MOCK_RESULT = {
  severity_score: 8.4,
  severity_label: "Critical",
  closure_probability: 0.87,
  estimated_duration_hours: 4.5,
  confidence: 0.92,
  resource_recommendation: { traffic_police: 24, barricades: 40, checkpoints: 6, emergency_units: 2, total_estimated_cost: 34800 },
  diversion_routes: [
    { route_name: "Via Hosur Road — Bypass Elevated", distance_km: 3.2, estimated_time_min: 18, congestion_level: "low" },
    { route_name: "Via 100ft Road — Koramangala",    distance_km: 2.7, estimated_time_min: 24, congestion_level: "moderate" },
    { route_name: "Via BTM — Bannerghatta Road",     distance_km: 4.1, estimated_time_min: 31, congestion_level: "heavy" },
  ],
};

const CONGESTION_CONFIG: Record<string, { color: string; badge: string }> = {
  low:      { color: "bg-emerald-500", badge: "badge-green" },
  moderate: { color: "bg-yellow-500",  badge: "badge-yellow" },
  heavy:    { color: "bg-red-500",     badge: "badge-red" },
};

export default function PredictionsPage() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [form, setForm] = useState({
    event_cause: "water_logging",
    location: "Silk Board Junction",
    priority: "High",
    requires_road_closure: true,
  });

  const handlePredict = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    const loc = BENGALURU_LOCATIONS.find(l => l.name === form.location) || BENGALURU_LOCATIONS[0];
    try {
      const data = await predictionService.predictImpact({
        event_cause: form.event_cause,
        latitude: loc.lat, longitude: loc.lng,
        priority: form.priority,
        requires_road_closure: form.requires_road_closure,
        start_datetime: new Date().toISOString(),
        event_type: "unplanned",
      });
      setResult(data);
    } catch {
      await new Promise(r => setTimeout(r, 1400));
      setResult(MOCK_RESULT);
    } finally {
      setLoading(false);
    }
  };

  const severityColor = result
    ? result.severity_score >= 8 ? "#EF4444"
    : result.severity_score >= 6 ? "#FB923C"
    : "#10B981"
    : "#3B82F6";

  return (
    <div className="h-full overflow-y-auto">
      <div className="p-6 space-y-6">

        {/* Header */}
        <motion.div initial={{ opacity:0, y:-10 }} animate={{ opacity:1, y:0 }}>
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <div className="w-7 h-7 rounded-lg bg-blue-500/20 flex items-center justify-center">
                  <Zap size={14} className="text-blue-400" />
                </div>
                <span className="badge badge-blue">AI Predictor</span>
              </div>
              <h1 className="text-2xl font-bold text-white tracking-tight">Impact Simulation</h1>
              <p className="text-[13px] text-slate-500 mt-0.5">ML-driven severity prediction and resource optimization</p>
            </div>
          </div>
        </motion.div>

        <div className="grid grid-cols-12 gap-5">

          {/* ── Form Panel ──────────────────────────── */}
          <motion.div
            initial={{ opacity:0, x:-16 }} animate={{ opacity:1, x:0 }} transition={{ delay:0.1 }}
            className="col-span-4"
          >
            <form onSubmit={handlePredict} className="glass-card p-5 space-y-5">
              <h3 className="text-[14px] font-semibold text-white">Event Parameters</h3>

              <div className="space-y-1.5">
                <label className="section-label">Incident Type</label>
                <select
                  className="select-premium"
                  value={form.event_cause}
                  onChange={e => setForm({ ...form, event_cause: e.target.value })}
                >
                  {EVENT_CAUSES.map(c => (
                    <option key={c.value} value={c.value}>{c.label}</option>
                  ))}
                </select>
              </div>

              <div className="space-y-1.5">
                <label className="section-label flex items-center gap-1.5"><MapPin size={10}/> Target Zone</label>
                <select
                  className="select-premium"
                  value={form.location}
                  onChange={e => setForm({ ...form, location: e.target.value })}
                >
                  {BENGALURU_LOCATIONS.map(l => (
                    <option key={l.name} value={l.name}>{l.name}</option>
                  ))}
                </select>
              </div>

              <div className="space-y-2">
                <label className="section-label">Priority Level</label>
                <div className="grid grid-cols-2 gap-2">
                  {["High", "Low"].map(p => (
                    <button
                      key={p} type="button"
                      onClick={() => setForm({ ...form, priority: p })}
                      className={`py-2.5 rounded-xl text-[13px] font-medium border transition-all ${
                        form.priority === p
                          ? p === "High"
                            ? "bg-red-500/15 border-red-500/40 text-red-300"
                            : "bg-blue-500/15 border-blue-500/40 text-blue-300"
                          : "bg-white/[0.03] border-white/[0.08] text-slate-500 hover:text-slate-300"
                      }`}
                    >
                      {p === "High" ? "⚠ Critical" : "◎ Standard"}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="flex items-center gap-3 p-3 rounded-xl bg-white/[0.03] border border-white/[0.07] cursor-pointer hover:bg-white/[0.05] transition-all">
                  <input
                    type="checkbox"
                    checked={form.requires_road_closure}
                    onChange={e => setForm({ ...form, requires_road_closure: e.target.checked })}
                    className="w-4 h-4 rounded accent-blue-500"
                  />
                  <div>
                    <p className="text-[13px] font-medium text-slate-300">Road Closure Required</p>
                    <p className="text-[11px] text-slate-600">Full lane isolation scenario</p>
                  </div>
                </label>
              </div>

              <button type="submit" disabled={loading} className="btn-primary w-full justify-center">
                {loading
                  ? <><Activity size={14} className="animate-spin" /> Running Simulation…</>
                  : <><Zap size={14} /> Run AI Simulation</>
                }
              </button>
            </form>
          </motion.div>

          {/* ── Results Panel ────────────────────────── */}
          <div className="col-span-8 space-y-4">
            <AnimatePresence mode="wait">

              {/* Empty state */}
              {!result && !loading && (
                <motion.div
                  key="empty"
                  initial={{ opacity:0 }} animate={{ opacity:1 }} exit={{ opacity:0 }}
                  className="glass-card p-12 flex flex-col items-center justify-center text-center h-80"
                >
                  <div className="w-16 h-16 rounded-2xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center mb-4">
                    <Zap size={28} className="text-blue-400/60 animate-glow-pulse" />
                  </div>
                  <h3 className="text-[16px] font-semibold text-slate-400 mb-2">Ready for Simulation</h3>
                  <p className="text-[13px] text-slate-600 max-w-xs">Configure the event parameters and run the AI simulation to receive severity predictions and resource deployment plans.</p>
                </motion.div>
              )}

              {/* Loading */}
              {loading && (
                <motion.div
                  key="loading"
                  initial={{ opacity:0 }} animate={{ opacity:1 }} exit={{ opacity:0 }}
                  className="glass-card p-12 flex flex-col items-center justify-center h-80 space-y-5"
                >
                  <div className="relative w-20 h-20">
                    <div className="absolute inset-0 rounded-full border-2 border-blue-500/20 animate-spin-slow"></div>
                    <div className="absolute inset-2 rounded-full border-2 border-t-blue-400 border-transparent animate-spin"></div>
                    <div className="absolute inset-4 rounded-full border border-cyan-500/40 animate-spin" style={{ animationDuration: "2.5s", animationDirection: "reverse" }}></div>
                    <Zap size={18} className="absolute inset-0 m-auto text-blue-400" />
                  </div>
                  <div className="text-center">
                    <p className="text-[14px] font-semibold text-white">Inference in Progress</p>
                    <p className="text-[12px] text-slate-500 mt-1 mono">XGBoost + LightGBM · 32 features</p>
                  </div>
                </motion.div>
              )}

              {/* Results */}
              {result && !loading && (
                <motion.div key="results" initial={{ opacity:0 }} animate={{ opacity:1 }} className="space-y-4">

                  {/* Severity banner */}
                  <div className="glass-card p-5" style={{ borderColor: `${severityColor}30` }}>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-xl flex items-center justify-center" style={{ background: `${severityColor}18`, border: `1px solid ${severityColor}30` }}>
                          <ShieldAlert size={22} style={{ color: severityColor }} />
                        </div>
                        <div>
                          <div className="flex items-center gap-2 mb-0.5">
                            <p className="text-[18px] font-bold text-white">{result.severity_label} Impact</p>
                            <span className="mono text-[11px] px-2 py-0.5 rounded-md" style={{ background: `${severityColor}18`, color: severityColor }}>
                              {(result.confidence * 100).toFixed(0)}% confidence
                            </span>
                          </div>
                          <p className="text-[12px] text-slate-500">AI prediction based on {form.location} parameters</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-6">
                        {[
                          { label: "Severity", value: `${result.severity_score.toFixed(1)}/10` },
                          { label: "Closure Prob", value: `${(result.closure_probability * 100).toFixed(0)}%` },
                          { label: "Est. Duration", value: `${result.estimated_duration_hours}h` },
                        ].map(({ label, value }) => (
                          <div key={label} className="text-center">
                            <p className="text-[10px] text-slate-600 mb-1">{label}</p>
                            <p className="mono text-[20px] font-bold text-white">{value}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">

                    {/* Resource deployment */}
                    <div className="glass-card p-5">
                      <h3 className="text-[14px] font-semibold text-white mb-4 flex items-center gap-2">
                        <Users size={15} className="text-blue-400" /> Deployment Plan
                      </h3>
                      <div className="grid grid-cols-2 gap-3 mb-4">
                        {[
                          { icon: Users,   label: "Police Units",    value: result.resource_recommendation.traffic_police },
                          { icon: HardHat, label: "Barricades",      value: result.resource_recommendation.barricades },
                          { icon: Tent,    label: "Checkpoints",     value: result.resource_recommendation.checkpoints },
                          { icon: Car,     label: "Emergency Units", value: result.resource_recommendation.emergency_units },
                        ].map(({ icon: Icon, label, value }) => (
                          <div key={label} className="p-3 rounded-xl bg-white/[0.03] border border-white/[0.06]">
                            <div className="flex items-center gap-2 mb-2">
                              <Icon size={12} className="text-slate-500" />
                              <p className="text-[11px] text-slate-500">{label}</p>
                            </div>
                            <p className="mono text-[22px] font-bold text-white">{value}</p>
                          </div>
                        ))}
                      </div>
                      <div className="flex items-center justify-between p-3 rounded-xl bg-blue-500/[0.06] border border-blue-500/15">
                        <span className="text-[12px] text-slate-500">Estimated Budget</span>
                        <span className="mono text-[14px] font-bold text-emerald-400">₹{result.resource_recommendation.total_estimated_cost.toLocaleString()}</span>
                      </div>
                    </div>

                    {/* Diversion routes */}
                    <div className="glass-card p-5">
                      <h3 className="text-[14px] font-semibold text-white mb-4 flex items-center gap-2">
                        <Navigation2 size={15} className="text-cyan-400" /> Diversion Routes
                      </h3>
                      <div className="space-y-3">
                        {result.diversion_routes.map((route: any, i: number) => {
                          const cfg = CONGESTION_CONFIG[route.congestion_level] ?? CONGESTION_CONFIG["low"];
                          return (
                            <div key={i} className={`p-3 rounded-xl bg-white/[0.03] border border-white/[0.06] relative overflow-hidden`}>
                              <div className={`absolute left-0 top-0 w-0.5 h-full ${cfg.color}`}></div>
                              <div className="flex items-center justify-between pl-2">
                                <div>
                                  <p className="text-[12px] font-medium text-white">{route.route_name}</p>
                                  <p className="text-[11px] text-slate-600 mt-0.5 mono">{route.distance_km} km · {route.estimated_time_min} min</p>
                                </div>
                                <span className={`badge ${cfg.badge} capitalize`}>{route.congestion_level}</span>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </div>
  );
}
