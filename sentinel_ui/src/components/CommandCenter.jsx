import React from 'react';
import { 
  ShieldAlert, Video, Car, Activity, Zap, CheckCircle2, 
  ArrowUpRight, AlertTriangle, Radio, Server, Eye, TrendingUp, Cpu, Map
} from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

const TRAFFIC_TRENDS = [
  { time: '06:00', vehicles: 450, threats: 1 },
  { time: '08:00', vehicles: 1240, threats: 3 },
  { time: '10:00', vehicles: 1560, threats: 5 },
  { time: '12:00', vehicles: 1380, threats: 2 },
  { time: '14:00', vehicles: 1420, threats: 4 },
  { time: '16:00', vehicles: 1890, threats: 7 },
  { time: '18:00', vehicles: 2150, threats: 9 },
  { time: '20:00', vehicles: 1650, threats: 3 },
];

export default function CommandCenter({ onNavigate }) {
  return (
    <div className="p-4 space-y-4 max-w-[1920px] mx-auto font-mono text-xs">
      
      {/* Top Banner */}
      <div className="bg-command-card p-4 rounded-xl border border-command-border flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping" />
            <h2 className="font-extrabold text-slate-100 text-base uppercase tracking-wider">
              STATEWIDE SURVEILLANCE COMMAND CENTER (C3)
            </h2>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Real-time neural intelligence, live ANPR telemetry & statewide incident response matrix
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button 
            onClick={() => onNavigate('live-cameras')}
            className="px-4 py-2 bg-cyan-500/20 hover:bg-cyan-500/30 border border-cyan-500/40 text-cyan-300 rounded-lg font-bold flex items-center gap-1.5 transition shadow-glow-cyan"
          >
            <Video className="w-4 h-4" /> LAUNCH LIVE GRID
          </button>
          <button 
            onClick={() => onNavigate('alerts')}
            className="px-4 py-2 bg-rose-500/20 hover:bg-rose-500/30 border border-rose-500/40 text-rose-300 rounded-lg font-bold flex items-center gap-1.5 transition"
          >
            <ShieldAlert className="w-4 h-4" /> ACTIVE ALERTS (12)
          </button>
        </div>
      </div>

      {/* 4 Stat KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-command-card p-4 rounded-xl border border-command-border space-y-2">
          <div className="flex justify-between items-start">
            <span className="text-slate-400 text-[11px]">ACTIVE CCTV NODES</span>
            <div className="p-2 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
              <Radio className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-extrabold text-slate-100">1,420 <span className="text-xs text-emerald-400 font-normal">/ 1,420 ONLINE</span></div>
          <div className="text-[10px] text-slate-400 flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3 text-emerald-400" /> 100% NETWORK UPTIME
          </div>
        </div>

        <div className="bg-command-card p-4 rounded-xl border border-command-border space-y-2">
          <div className="flex justify-between items-start">
            <span className="text-slate-400 text-[11px]">ANPR DETECTIONS (24H)</span>
            <div className="p-2 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
              <Car className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-extrabold text-cyan-300">184,920 <span className="text-xs text-cyan-400 font-normal">VEHICLES</span></div>
          <div className="text-[10px] text-emerald-400 flex items-center gap-1">
            <TrendingUp className="w-3 h-3" /> +14.2% FLOW FROM YESTERDAY
          </div>
        </div>

        <div className="bg-command-card p-4 rounded-xl border border-command-border space-y-2">
          <div className="flex justify-between items-start">
            <span className="text-slate-400 text-[11px]">ACTIVE THREAT ALERTS</span>
            <div className="p-2 rounded bg-rose-500/10 text-rose-400 border border-rose-500/30">
              <ShieldAlert className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-extrabold text-rose-400">12 <span className="text-xs text-rose-300 font-normal">INCIDENTS</span></div>
          <div className="text-[10px] text-rose-400 flex items-center gap-1">
            <AlertTriangle className="w-3 h-3" /> 3 CRITICAL (PCR DISPATCHED)
          </div>
        </div>

        <div className="bg-command-card p-4 rounded-xl border border-command-border space-y-2">
          <div className="flex justify-between items-start">
            <span className="text-slate-400 text-[11px]">AI INFERENCE LATENCY</span>
            <div className="p-2 rounded bg-purple-500/10 text-purple-400 border border-purple-500/30">
              <Cpu className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-extrabold text-purple-300">12.4 ms <span className="text-xs text-slate-400 font-normal">YOLOv11</span></div>
          <div className="text-[10px] text-emerald-400 flex items-center gap-1">
            <Zap className="w-3 h-3" /> HARDWARE ACCELERATED
          </div>
        </div>
      </div>

      {/* Main Grid: Live Traffic Volume vs Recent ANPR Watchlist Hits */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        
        {/* Statewide Traffic & Threat Chart (2 Columns) */}
        <div className="lg:col-span-2 bg-command-card p-4 rounded-xl border border-command-border space-y-3">
          <div className="flex justify-between items-center border-b border-command-border pb-3">
            <h3 className="font-bold text-slate-200 flex items-center gap-2">
              <Activity className="w-4 h-4 text-cyan-400" /> STATEWIDE TRAFFIC FLOW VS THREAT INCIDENTS
            </h3>
            <span className="text-[10px] text-slate-400">HOURLY DISTRIBUTION</span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={TRAFFIC_TRENDS}>
                <defs>
                  <linearGradient id="colorVehicles" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#00f2fe" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#00f2fe" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorThreats" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ff2a6d" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#ff2a6d" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis dataKey="time" stroke="#64748b" />
                <YAxis stroke="#64748b" />
                <Tooltip contentStyle={{ backgroundColor: '#0c1220', borderColor: '#1a2744', color: '#e2e8f0' }} />
                <Area type="monotone" dataKey="vehicles" stroke="#00f2fe" fillOpacity={1} fill="url(#colorVehicles)" />
                <Area type="monotone" dataKey="threats" stroke="#ff2a6d" fillOpacity={1} fill="url(#colorThreats)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <div className="flex items-center justify-between text-[11px] text-slate-400 pt-2 border-t border-command-border">
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1.5 text-cyan-400">
                <span className="w-2.5 h-2.5 rounded-full bg-cyan-400" /> TOTAL VEHICLES SCANNED
              </span>
              <span className="flex items-center gap-1.5 text-rose-400">
                <span className="w-2.5 h-2.5 rounded-full bg-rose-500" /> THREAT DETECTION RATE
              </span>
            </div>
            <span className="text-emerald-400 font-bold">ACCURACY: 99.1%</span>
          </div>
        </div>

        {/* Right Side: Quick Action Live CCTV Matrix */}
        <div className="bg-command-card p-4 rounded-xl border border-command-border space-y-3">
          <div className="flex justify-between items-center border-b border-command-border pb-3">
            <h3 className="font-bold text-slate-200 flex items-center gap-2">
              <Eye className="w-4 h-4 text-cyan-400" /> HIGH-PRIORITY CAMERAS
            </h3>
            <button 
              onClick={() => onNavigate('live-cameras')}
              className="text-[10px] text-cyan-400 hover:underline"
            >
              VIEW ALL (6)
            </button>
          </div>

          <div className="space-y-2">
            {[
              { id: 'CAM-001', name: 'SG Highway Iskcon', city: 'Ahmedabad', status: 'ALERT ACTIVE', speed: '82 km/h' },
              { id: 'CAM-004', name: 'Express Toll Plaza', city: 'Vadodara', status: 'OVERSPEED', speed: '104 km/h' },
              { id: 'CAM-003', name: 'Textile Market Circle', city: 'Surat', status: 'CONGESTION', speed: '28 km/h' },
              { id: 'CAM-002', name: 'Sabarmati Riverfront', city: 'Ahmedabad', status: 'NORMAL', speed: '42 km/h' },
            ].map((c) => (
              <div 
                key={c.id} 
                onClick={() => onNavigate('live-cameras')}
                className="p-2.5 rounded-lg bg-command-bg border border-command-border hover:border-cyan-500/60 cursor-pointer flex items-center justify-between transition"
              >
                <div>
                  <div className="font-bold text-cyan-300">{c.id}: {c.name}</div>
                  <div className="text-[10px] text-slate-400">{c.city} • Avg: {c.speed}</div>
                </div>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                  c.status.includes('ALERT') ? 'bg-rose-500/20 text-rose-400 border border-rose-500/40' :
                  c.status.includes('OVERSPEED') ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40' :
                  'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                }`}>
                  {c.status}
                </span>
              </div>
            ))}
          </div>

          <button
            onClick={() => onNavigate('gis')}
            className="w-full py-2 bg-command-bg border border-command-border hover:border-cyan-500 text-slate-300 hover:text-cyan-300 rounded-lg text-center font-bold transition flex items-center justify-center gap-1.5"
          >
            <Map className="w-3.5 h-3.5" /> OPEN GEOSPATIAL RADAR
          </button>
        </div>

      </div>

    </div>
  );
}
