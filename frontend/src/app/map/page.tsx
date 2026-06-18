import dynamic from "next/dynamic";
import { Map } from "lucide-react";

const MapComponent = dynamic(() => import("@/components/MapComponent"), {
  ssr: false,
  loading: () => (
    <div className="h-full w-full flex flex-col items-center justify-center text-slate-500">
      <div className="w-10 h-10 rounded-2xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center mb-3 animate-pulse">
        <Map size={18} className="text-blue-400" />
      </div>
      <p className="text-[13px] font-medium text-slate-400">Loading geospatial map…</p>
      <p className="text-[11px] text-slate-600 mt-1 mono">Connecting to tile server</p>
    </div>
  ),
});

export default function MapPage() {
  return (
    <div className="h-full flex flex-col p-6 gap-5">

      {/* Header */}
      <div className="flex items-center justify-between flex-shrink-0">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <div className="w-7 h-7 rounded-lg bg-emerald-500/20 flex items-center justify-center">
              <Map size={14} className="text-emerald-400" />
            </div>
            <span className="badge badge-green">Live</span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Geospatial Intelligence</h1>
          <p className="text-[13px] text-slate-500 mt-0.5">Real-time incident mapping across Bengaluru</p>
        </div>

        {/* Legend */}
        <div className="glass-sm px-4 py-3 flex items-center gap-5">
          {[
            { color: "bg-red-500",    label: "Critical" },
            { color: "bg-orange-400", label: "High" },
            { color: "bg-yellow-400", label: "Medium" },
            { color: "bg-blue-400",   label: "Low" },
          ].map(({ color, label }) => (
            <div key={label} className="flex items-center gap-2">
              <div className={`w-2.5 h-2.5 rounded-full ${color}`}></div>
              <span className="text-[12px] text-slate-400">{label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Map container */}
      <div className="flex-1 glass-card overflow-hidden" style={{ minHeight: 0 }}>
        <MapComponent />
      </div>
    </div>
  );
}
