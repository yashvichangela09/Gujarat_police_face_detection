import React from 'react';
import { Activity, Cpu, Server, HardDrive, Wifi, CheckCircle2, Zap } from 'lucide-react';

export default function SystemHealth() {
  return (
    <div className="p-4 space-y-4 max-w-[1920px] mx-auto font-mono text-xs">
      
      {/* Top Banner */}
      <div className="bg-command-card p-4 rounded-xl border border-command-border flex items-center justify-between">
        <div>
          <h2 className="font-extrabold text-slate-100 text-base uppercase tracking-wider flex items-center gap-2">
            <Activity className="w-5 h-5 text-cyan-400" /> SYSTEM HEALTH & NEURAL CLUSTER DIAGNOSTICS
          </h2>
          <p className="text-xs text-slate-400">
            Real-time hardware telemetry, GPU VRAM load, inference latency & database pool health
          </p>
        </div>
        <span className="px-3 py-1.5 rounded-lg bg-emerald-950/60 border border-emerald-500/40 text-emerald-400 font-bold flex items-center gap-1.5">
          <CheckCircle2 className="w-4 h-4" /> ALL CLUSTERS OPERATIONAL
        </span>
      </div>

      {/* Hardware Telemetry Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        
        {/* GPU VRAM Load */}
        <div className="bg-command-card p-5 rounded-xl border border-command-border space-y-3">
          <div className="flex justify-between items-center text-slate-400">
            <span>NVIDIA GPU CLUSTER</span>
            <Cpu className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-extrabold text-cyan-300">42% <span className="text-xs font-normal text-slate-400">UTILIZATION</span></div>
          <div className="w-full bg-command-bg rounded-full h-2 border border-command-border overflow-hidden">
            <div className="bg-cyan-400 h-full rounded-full" style={{ width: '42%' }} />
          </div>
          <div className="flex justify-between text-[10px] text-slate-400">
            <span>VRAM: 10.2 / 24 GB</span>
            <span className="text-emerald-400">TEMP: 48°C</span>
          </div>
        </div>

        {/* CPU Load */}
        <div className="bg-command-card p-5 rounded-xl border border-command-border space-y-3">
          <div className="flex justify-between items-center text-slate-400">
            <span>HOST CPU (AMD EPYC)</span>
            <Zap className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-extrabold text-emerald-300">28% <span className="text-xs font-normal text-slate-400">64 CORES</span></div>
          <div className="w-full bg-command-bg rounded-full h-2 border border-command-border overflow-hidden">
            <div className="bg-emerald-400 h-full rounded-full" style={{ width: '28%' }} />
          </div>
          <div className="flex justify-between text-[10px] text-slate-400">
            <span>RAM: 34.8 / 128 GB</span>
            <span className="text-emerald-400">LOAD: 1.42</span>
          </div>
        </div>

        {/* NVMe Storage Array */}
        <div className="bg-command-card p-5 rounded-xl border border-command-border space-y-3">
          <div className="flex justify-between items-center text-slate-400">
            <span>NVMe CCTV ARCHIVE POOL</span>
            <HardDrive className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-extrabold text-amber-300">68% <span className="text-xs font-normal text-slate-400">CAPACITY</span></div>
          <div className="w-full bg-command-bg rounded-full h-2 border border-command-border overflow-hidden">
            <div className="bg-amber-400 h-full rounded-full" style={{ width: '68%' }} />
          </div>
          <div className="flex justify-between text-[10px] text-slate-400">
            <span>STORAGE: 164 / 240 TB</span>
            <span className="text-amber-400">RETENTION: 90 DAYS</span>
          </div>
        </div>

        {/* WebSocket Stream Bus */}
        <div className="bg-command-card p-5 rounded-xl border border-command-border space-y-3">
          <div className="flex justify-between items-center text-slate-400">
            <span>WEBSOCKET & RTSP BUS</span>
            <Wifi className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-extrabold text-purple-300">0.8 ms <span className="text-xs font-normal text-slate-400">LATENCY</span></div>
          <div className="w-full bg-command-bg rounded-full h-2 border border-command-border overflow-hidden">
            <div className="bg-purple-400 h-full rounded-full" style={{ width: '92%' }} />
          </div>
          <div className="flex justify-between text-[10px] text-slate-400">
            <span>CONCURRENCY: 240 CONNS</span>
            <span className="text-emerald-400">0 PACKET LOSS</span>
          </div>
        </div>

      </div>

      {/* Services Health Breakdown Table */}
      <div className="bg-command-card p-5 rounded-xl border border-command-border space-y-3">
        <h3 className="font-bold text-slate-200 border-b border-command-border pb-3 flex items-center gap-2">
          <Server className="w-4 h-4 text-cyan-400" /> CORE MICROSERVICES STATUS MATRIX
        </h3>

        <div className="space-y-2">
          {[
            { service: 'FastAPI AI Engine (Port 8100)', endpoint: 'http://127.0.0.1:8100', status: 'RUNNING', latency: '0.4ms', memory: '1.2 GB' },
            { service: 'YOLOv11 TensorRT Worker Daemon', endpoint: 'IPC / Shared Memory', status: 'RUNNING', latency: '12.4ms', memory: '4.8 GB' },
            { service: 'Vite React Command Center Web App', endpoint: 'http://localhost:5173', status: 'RUNNING', latency: '1.1ms', memory: '85 MB' },
            { service: 'PostgreSQL Database & ANPR Detections', endpoint: 'postgresql://127.0.0.1:5432', status: 'CONNECTED', latency: '0.6ms', memory: '820 MB' },
            { service: 'RTSP Stream Demuxer & Transcoder', endpoint: 'rtsp://10.42.0.0/matrix', status: 'RUNNING', latency: '2.1ms', memory: '2.4 GB' },
          ].map((s) => (
            <div key={s.service} className="p-3 bg-command-bg rounded-lg border border-command-border flex items-center justify-between">
              <div>
                <div className="font-bold text-slate-100">{s.service}</div>
                <div className="text-[10px] text-slate-400">{s.endpoint}</div>
              </div>
              <div className="flex items-center gap-6">
                <span className="text-slate-400 text-[11px] hidden sm:inline">MEM: {s.memory}</span>
                <span className="text-cyan-300 font-semibold">{s.latency}</span>
                <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 text-[10px] font-bold">
                  ● {s.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

    </div>
  );
}
