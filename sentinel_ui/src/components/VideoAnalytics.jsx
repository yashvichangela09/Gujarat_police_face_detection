import React from 'react';
import { BarChart3, Users, Car, Gauge, Eye, TrendingUp, PieChart as PieIcon, Activity } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

const VEHICLE_CLASS_DATA = [
  { name: 'Sedan/Hatchback', value: 48, color: '#00f2fe' },
  { name: 'SUV / MUV', value: 24, color: '#00f5d4' },
  { name: 'Two-Wheeler', value: 16, color: '#ffb703' },
  { name: 'Heavy Trucks', value: 8, color: '#ff2a6d' },
  { name: 'Buses (GSRTC)', value: 4, color: '#9d4edd' },
];

const SPEED_DISTRIBUTION = [
  { range: '< 40 km/h', count: 320 },
  { range: '40-60 km/h', count: 1140 },
  { range: '60-80 km/h', count: 860 },
  { range: '80-100 km/h', count: 240 },
  { range: '> 100 km/h (Violation)', count: 45 },
];

export default function VideoAnalytics() {
  return (
    <div className="p-4 space-y-4 max-w-[1920px] mx-auto font-mono text-xs">
      
      {/* Top Banner */}
      <div className="bg-command-card p-4 rounded-xl border border-command-border flex items-center justify-between">
        <div>
          <h2 className="font-extrabold text-slate-100 text-base uppercase tracking-wider flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-cyan-400" /> AI VIDEO ANALYTICS & STATISTICAL INTELLIGENCE
          </h2>
          <p className="text-xs text-slate-400">
            Automated neural crowd density, velocity profiling, vehicle classification & violation heatmaps
          </p>
        </div>
        <div className="text-emerald-400 font-bold bg-emerald-950/40 border border-emerald-500/40 px-3 py-1.5 rounded-lg">
          MODEL: YOLOv11 STATEWIDE BATCH INFERENCE
        </div>
      </div>

      {/* Analytics KPI Row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-command-card p-4 rounded-xl border border-command-border">
          <div className="flex justify-between items-center text-slate-400 mb-1">
            <span>AVG HIGHWAY VELOCITY</span>
            <Gauge className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-extrabold text-amber-300">62.8 <span className="text-xs font-normal">KM/H</span></div>
          <p className="text-[10px] text-slate-400 mt-1">Speed compliance rate: 94.6%</p>
        </div>

        <div className="bg-command-card p-4 rounded-xl border border-command-border">
          <div className="flex justify-between items-center text-slate-400 mb-1">
            <span>PEAK CROWD DENSITY INDEX</span>
            <Users className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-extrabold text-cyan-300">140 <span className="text-xs font-normal">PPL / 100m²</span></div>
          <p className="text-[10px] text-slate-400 mt-1">Sabarmati Riverfront Promenade</p>
        </div>

        <div className="bg-command-card p-4 rounded-xl border border-command-border">
          <div className="flex justify-between items-center text-slate-400 mb-1">
            <span>AI OBJECT RECOGNITION ACCURACY</span>
            <Eye className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-extrabold text-emerald-400">98.92%</div>
          <p className="text-[10px] text-slate-400 mt-1">YOLOv11 TensorRT Engine</p>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        
        {/* Vehicle Classification Breakdown */}
        <div className="bg-command-card p-4 rounded-xl border border-command-border space-y-3">
          <h3 className="font-bold text-slate-200 flex items-center gap-2 border-b border-command-border pb-2">
            <PieIcon className="w-4 h-4 text-cyan-400" /> VEHICLE CLASSIFICATION DISTRIBUTION
          </h3>

          <div className="h-60 w-full flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={VEHICLE_CLASS_DATA}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={85}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {VEHICLE_CLASS_DATA.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: '#0c1220', borderColor: '#1a2744', color: '#e2e8f0' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 pt-2 border-t border-command-border">
            {VEHICLE_CLASS_DATA.map((item) => (
              <div key={item.name} className="flex items-center gap-2 text-[10px]">
                <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: item.color }} />
                <span className="text-slate-300 truncate">{item.name}: <b>{item.value}%</b></span>
              </div>
            ))}
          </div>
        </div>

        {/* Speed Distribution Histogram */}
        <div className="bg-command-card p-4 rounded-xl border border-command-border space-y-3">
          <h3 className="font-bold text-slate-200 flex items-center gap-2 border-b border-command-border pb-2">
            <BarChart3 className="w-4 h-4 text-amber-400" /> RADAR SPEED PROFILING & VIOLATIONS
          </h3>

          <div className="h-60 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={SPEED_DISTRIBUTION}>
                <XAxis dataKey="range" stroke="#64748b" />
                <YAxis stroke="#64748b" />
                <Tooltip contentStyle={{ backgroundColor: '#0c1220', borderColor: '#1a2744', color: '#e2e8f0' }} />
                <Bar dataKey="count" fill="#00f2fe" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="flex justify-between items-center text-[11px] text-slate-400 pt-2 border-t border-command-border">
            <span>AUTOMATED E-CHALLAN SPEED LIMIT: 80 KM/H</span>
            <span className="text-rose-400 font-bold">45 VIOLATIONS DETECTED</span>
          </div>
        </div>

      </div>

    </div>
  );
}
