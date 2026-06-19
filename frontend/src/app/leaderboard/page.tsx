"use client";

import { useEffect, useState } from "react";
import { analyticsService } from "@/lib/api";
import { motion } from "framer-motion";
import { Shield, Medal, TrendingUp, TrendingDown, Clock, Activity, AlertTriangle } from "lucide-react";

export default function LeaderboardPage() {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    async function loadData() {
      try {
        const res = await analyticsService.getLeaderboard();
        setData(res);
      } catch (e) {
        // Fallback mock if backend is not running yet
        setTimeout(() => {
          setData({
            total_stations: 15,
            leaderboard: [
              { station: "Koramangala Traffic PS", event_count: 342, efficiency_score: 0.82, avg_delay_hours: -0.8, rank: 1 },
              { station: "Indiranagar Traffic PS", event_count: 289, efficiency_score: 0.88, avg_delay_hours: -0.5, rank: 2 },
              { station: "HSR Layout Traffic PS", event_count: 410, efficiency_score: 0.94, avg_delay_hours: -0.2, rank: 3 },
              { station: "Whitefield Traffic PS", event_count: 512, efficiency_score: 0.99, avg_delay_hours: 0.0, rank: 4 },
              { station: "Madiwala Traffic PS", event_count: 476, efficiency_score: 1.05, avg_delay_hours: 0.3, rank: 5 },
              { station: "Electronic City Traffic PS", event_count: 220, efficiency_score: 1.15, avg_delay_hours: 1.2, rank: 6 },
              { station: "Silk Board Unit", event_count: 630, efficiency_score: 1.28, avg_delay_hours: 2.1, rank: 7 },
            ]
          });
          setLoading(false);
        }, 800);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  return (
    <div className="h-full overflow-y-auto">
      <div className="p-6 max-w-5xl mx-auto space-y-6">
        
        {/* Header */}
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <div className="w-7 h-7 rounded-lg bg-indigo-500/20 flex items-center justify-center">
                <Shield size={14} className="text-indigo-400" />
              </div>
              <span className="badge bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">Operational Intel</span>
            </div>
            <h1 className="text-2xl font-bold text-white tracking-tight">Jurisdiction Leaderboard</h1>
            <p className="text-[13px] text-slate-500 mt-0.5">Machine Learning evaluation of police station efficiency</p>
          </div>
          
          <div className="flex items-center gap-4 bg-white/[0.02] border border-white/[0.05] rounded-xl p-3 px-5">
            <div className="text-right">
              <p className="text-[10px] text-slate-500 uppercase font-semibold">Active Units</p>
              <p className="mono text-[18px] font-bold text-white">{data?.total_stations || "--"}</p>
            </div>
            <div className="w-px h-8 bg-white/[0.08]"></div>
            <div className="text-right">
              <p className="text-[10px] text-slate-500 uppercase font-semibold">Evaluation Model</p>
              <p className="text-[13px] font-medium text-indigo-400">XGBoost Baseline</p>
            </div>
          </div>
        </motion.div>

        {loading ? (
          <div className="glass-card p-12 flex flex-col items-center justify-center h-64">
            <Activity className="text-indigo-400 animate-pulse mb-4" size={32} />
            <p className="text-white font-medium">Computing Efficiency Scores...</p>
          </div>
        ) : (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}>
            
            {/* Top 3 Podium */}
            <div className="grid grid-cols-3 gap-4 mb-6">
              {data?.leaderboard.slice(0, 3).map((station: any, idx: number) => (
                <div key={station.station} className="glass-card relative overflow-hidden group">
                  <div className={`absolute top-0 left-0 w-full h-1 ${idx === 0 ? 'bg-amber-400' : idx === 1 ? 'bg-slate-300' : 'bg-orange-400'}`}></div>
                  <div className="p-5">
                    <div className="flex justify-between items-start mb-4">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center text-[12px] font-bold ${
                        idx === 0 ? 'bg-amber-400/20 text-amber-400 border border-amber-400/30' : 
                        idx === 1 ? 'bg-slate-300/20 text-slate-300 border border-slate-300/30' : 
                        'bg-orange-400/20 text-orange-400 border border-orange-400/30'
                      }`}>
                        #{station.rank}
                      </div>
                      <Medal size={20} className={idx === 0 ? 'text-amber-400' : idx === 1 ? 'text-slate-300' : 'text-orange-400'} />
                    </div>
                    <h3 className="text-[15px] font-bold text-white mb-1 truncate">{station.station}</h3>
                    <div className="flex items-center gap-2 text-[12px] text-slate-400">
                      <Activity size={12} /> {station.event_count} incidents resolved
                    </div>
                    
                    <div className="mt-4 pt-4 border-t border-white/[0.06] flex justify-between items-end">
                      <div>
                        <p className="text-[10px] text-slate-500 uppercase">Efficiency Score</p>
                        <p className="mono text-[18px] font-bold text-emerald-400">{station.efficiency_score.toFixed(2)}</p>
                      </div>
                      <div className="text-right">
                        <span className="badge badge-green flex items-center gap-1">
                          <TrendingDown size={10} /> {Math.abs(station.avg_delay_hours).toFixed(1)}h faster
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Full List */}
            <div className="glass-card overflow-hidden">
              <div className="p-4 border-b border-white/[0.06] bg-white/[0.01]">
                <h3 className="text-[14px] font-semibold text-white">Full Jurisdiction Rankings</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-white/[0.06] text-[11px] text-slate-500 uppercase tracking-wider">
                      <th className="p-4 font-medium">Rank</th>
                      <th className="p-4 font-medium">Police Station</th>
                      <th className="p-4 font-medium text-right">Incidents Handled</th>
                      <th className="p-4 font-medium text-right">Avg ML Deviation</th>
                      <th className="p-4 font-medium text-right">Efficiency Score</th>
                      <th className="p-4 font-medium text-center">Status</th>
                    </tr>
                  </thead>
                  <tbody className="text-[13px]">
                    {data?.leaderboard.map((station: any) => {
                      const isGood = station.efficiency_score <= 1.0;
                      const isWarning = station.efficiency_score > 1.1;
                      
                      return (
                        <tr key={station.station} className="border-b border-white/[0.03] hover:bg-white/[0.02] transition-colors group">
                          <td className="p-4 mono text-slate-400">#{station.rank}</td>
                          <td className="p-4 font-medium text-slate-200">{station.station}</td>
                          <td className="p-4 mono text-right text-slate-400">{station.event_count}</td>
                          <td className="p-4 text-right">
                            <span className={`mono px-2 py-1 rounded text-[11px] ${
                              isGood ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'
                            }`}>
                              {station.avg_delay_hours > 0 ? '+' : ''}{station.avg_delay_hours.toFixed(1)}h
                            </span>
                          </td>
                          <td className="p-4 mono text-right font-bold text-white">
                            {station.efficiency_score.toFixed(2)}
                          </td>
                          <td className="p-4 text-center">
                            <div className="flex justify-center">
                              {isGood ? (
                                <div className="w-6 h-6 rounded-full bg-emerald-500/20 flex items-center justify-center">
                                  <TrendingDown size={12} className="text-emerald-400" />
                                </div>
                              ) : isWarning ? (
                                <div className="w-6 h-6 rounded-full bg-red-500/20 flex items-center justify-center">
                                  <AlertTriangle size={12} className="text-red-400" />
                                </div>
                              ) : (
                                <div className="w-6 h-6 rounded-full bg-slate-500/20 flex items-center justify-center">
                                  <Clock size={12} className="text-slate-400" />
                                </div>
                              )}
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

          </motion.div>
        )}
      </div>
    </div>
  );
}
