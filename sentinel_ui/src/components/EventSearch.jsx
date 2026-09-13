import React, { useState } from 'react';
import { Search, Filter, Calendar, BarChart2, PieChart, Download, FileText, CheckCircle2 } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';

const HOURLY_TRAFFIC_DATA = [
  { time: '00:00', count: 120, alerts: 1 },
  { time: '03:00', count: 45, alerts: 0 },
  { time: '06:00', count: 380, alerts: 2 },
  { time: '09:00', count: 1240, alerts: 5 },
  { time: '12:00', count: 980, alerts: 3 },
  { time: '15:00', count: 1100, alerts: 4 },
  { time: '18:00', count: 1450, alerts: 8 },
  { time: '21:00', count: 620, alerts: 2 },
];

const SEARCH_RESULTS = [
  { id: 10842, time: '09:06:12 IST', camera: 'CAM-001', label: 'Sedan (White)', plate: 'GJ-01-AB-1234', conf: '98.8%', status: 'STOLEN ALERT' },
  { id: 10841, time: '09:05:44 IST', camera: 'CAM-003', label: 'Motorcycle', plate: 'GJ-01-XY-5678', conf: '94.2%', status: 'NORMAL' },
  { id: 10840, time: '09:04:10 IST', camera: 'CAM-004', label: 'Heavy Truck', plate: 'GJ-05-CD-3321', conf: '99.4%', status: 'OVERSPEED' },
  { id: 10839, time: '09:02:01 IST', camera: 'CAM-002', label: 'Face Detected', plate: '—', conf: '89.5%', status: 'CROWD MONITOR' },
  { id: 10838, time: '08:59:30 IST', camera: 'CAM-006', label: 'SUV (Black)', plate: 'GJ-06-ZZ-9900', conf: '96.1%', status: 'NORMAL' },
];

export default function EventSearch() {
  const [searchTerm, setSearchTerm] = useState('');
  const [objectFilter, setObjectFilter] = useState('ALL');
  const [exportNotice, setExportNotice] = useState('');

  const handleExport = () => {
    setExportNotice('AI Search report exported to PDF/CSV archive.');
    setTimeout(() => setExportNotice(''), 3000);
  };

  return (
    <div className="p-4 space-y-4 max-w-[1920px] mx-auto font-mono text-xs">
      
      {/* Top Banner & Filter Form */}
      <div className="bg-command-card p-4 rounded-xl border border-command-border space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-command-border pb-3">
          <div>
            <h2 className="font-extrabold text-slate-100 text-base uppercase tracking-wider flex items-center gap-2">
              <Search className="w-5 h-5 text-cyan-400" /> AI EVENT LOG SEARCH & ANALYTICS DASHBOARD
            </h2>
            <p className="text-xs text-slate-400">
              Query millions of YOLO detections, license plate hits, and CCTV incident logs
            </p>
          </div>

          <button
            onClick={handleExport}
            className="px-3.5 py-1.5 bg-cyan-500/20 border border-cyan-500/40 text-cyan-300 rounded-lg hover:bg-cyan-500/30 flex items-center gap-1.5 transition"
          >
            <Download className="w-3.5 h-3.5" /> EXPORT ANALYTICS REPORT
          </button>
        </div>

        {/* Filter Inputs */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="SEARCH BY PLATE, CAMERA ID OR KEYWORD..."
              className="w-full pl-9 pr-3 py-2 bg-command-bg border border-command-border rounded-lg text-slate-200 focus:outline-none focus:border-cyan-500"
            />
          </div>

          <select
            value={objectFilter}
            onChange={(e) => setObjectFilter(e.target.value)}
            className="px-3 py-2 bg-command-bg border border-command-border rounded-lg text-slate-200 focus:outline-none focus:border-cyan-500"
          >
            <option value="ALL">FILTER BY OBJECT: ALL CLASSES</option>
            <option value="CAR">VEHICLES (CARS / SUVS)</option>
            <option value="TRUCK">HEAVY TRUCKS & BUSES</option>
            <option value="MOTORCYCLE">TWO-WHEELERS</option>
            <option value="FACE">FACE DETECTIONS</option>
          </select>

          <div className="flex items-center gap-2 bg-command-bg px-3 py-2 border border-command-border rounded-lg text-slate-400">
            <Calendar className="w-4 h-4 text-cyan-400" />
            <span>DATE: TODAY (LAST 24 HOURS)</span>
          </div>
        </div>

        {exportNotice && (
          <div className="bg-emerald-950 border border-emerald-500 text-emerald-300 p-2 rounded text-xs flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" /> {exportNotice}
          </div>
        )}
      </div>

      {/* Analytics Visual Charts (Recharts) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        
        {/* Hourly Traffic Volume Area Chart */}
        <div className="bg-command-card p-4 rounded-xl border border-command-border space-y-2">
          <h3 className="font-bold text-slate-200 flex items-center gap-2 border-b border-command-border pb-2">
            <BarChart2 className="w-4 h-4 text-cyan-400" /> HOURLY VEHICLE VOLUME (GUJARAT CCTV NETWORK)
          </h3>
          <div className="h-56 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={HOURLY_TRAFFIC_DATA}>
                <defs>
                  <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#00f2fe" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#00f2fe" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis dataKey="time" stroke="#64748b" />
                <YAxis stroke="#64748b" />
                <Tooltip contentStyle={{ backgroundColor: '#0c1220', borderColor: '#1a2744', color: '#e2e8f0' }} />
                <Area type="monotone" dataKey="count" stroke="#00f2fe" fillOpacity={1} fill="url(#colorCount)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Threat & Alert Count Bar Chart */}
        <div className="bg-command-card p-4 rounded-xl border border-command-border space-y-2">
          <h3 className="font-bold text-slate-200 flex items-center gap-2 border-b border-command-border pb-2">
            <PieChart className="w-4 h-4 text-rose-400" /> AI THREAT DETECTION INCIDENTS BY TIME
          </h3>
          <div className="h-56 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={HOURLY_TRAFFIC_DATA}>
                <XAxis dataKey="time" stroke="#64748b" />
                <YAxis stroke="#64748b" />
                <Tooltip contentStyle={{ backgroundColor: '#0c1220', borderColor: '#1a2744', color: '#e2e8f0' }} />
                <Bar dataKey="alerts" fill="#ff2a6d" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

      </div>

      {/* Query Results Table */}
      <div className="bg-command-card p-4 rounded-xl border border-command-border space-y-3">
        <h3 className="font-bold text-slate-200 flex items-center gap-2 border-b border-command-border pb-2">
          <FileText className="w-4 h-4 text-cyan-400" /> SEARCH MATCH LOG ARCHIVE
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-command-border text-slate-400 text-[11px]">
                <th className="py-2 px-3">LOG ID</th>
                <th className="py-2 px-3">TIMESTAMP</th>
                <th className="py-2 px-3">CAMERA NODE</th>
                <th className="py-2 px-3">DETECTION LABEL</th>
                <th className="py-2 px-3">PLATE NUMBER</th>
                <th className="py-2 px-3">CONFIDENCE</th>
                <th className="py-2 px-3">STATUS FLAG</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-command-border/40">
              {SEARCH_RESULTS.map((r) => (
                <tr key={r.id} className="hover:bg-command-bg/50 transition">
                  <td className="py-2.5 px-3 text-cyan-400 font-bold">#{r.id}</td>
                  <td className="py-2.5 px-3 text-slate-300">{r.time}</td>
                  <td className="py-2.5 px-3 text-slate-200">{r.camera}</td>
                  <td className="py-2.5 px-3 text-slate-300">{r.label}</td>
                  <td className="py-2.5 px-3 text-cyan-300 font-bold tracking-wider">{r.plate}</td>
                  <td className="py-2.5 px-3 text-emerald-400">{r.conf}</td>
                  <td className="py-2.5 px-3">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      r.status.includes('ALERT') ? 'bg-rose-500/20 text-rose-400 border border-rose-500/40' :
                      r.status.includes('OVERSPEED') ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40' :
                      'bg-slate-800 text-slate-400'
                    }`}>
                      {r.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
}
