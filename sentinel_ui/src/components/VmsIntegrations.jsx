import React, { useState } from 'react';
import { Cable, Server, CheckCircle2, AlertCircle, RefreshCw, Zap, ShieldCheck } from 'lucide-react';

const VMS_PROVIDERS = [
  { id: 'vms-1', name: 'Milestone XProtect Corporate', type: 'VMS Gateway', endpoint: 'https://vms-ahmedabad.police.gujarat.gov.in:8082', cameras: 480, status: 'CONNECTED', latency: '4ms' },
  { id: 'vms-2', name: 'Hikvision HikCentral Enterprise', type: 'ANPR Stream Hub', endpoint: 'https://hikcentral.surat.gov.in:443', cameras: 360, status: 'CONNECTED', latency: '6ms' },
  { id: 'vms-3', name: 'Dahua DSS Pro Platform', type: 'CCTV Matrix', endpoint: 'https://dss.vadodara.gov.in:8080', cameras: 290, status: 'CONNECTED', latency: '5ms' },
  { id: 'vms-4', name: 'ONVIF Profile S/G/T Bridge', type: 'Generic RTSP Relay', endpoint: 'rtsp://10.42.0.1:554/onvif', cameras: 180, status: 'CONNECTED', latency: '2ms' },
  { id: 'vms-5', name: 'Axis Camera Station Pro', type: 'Radar & PTZ Gateway', endpoint: 'https://acs.gandhinagar.gov.in:8443', cameras: 110, status: 'CONNECTED', latency: '3ms' },
];

export default function VmsIntegrations() {
  const [syncing, setSyncing] = useState(false);

  const triggerSync = () => {
    setSyncing(true);
    setTimeout(() => setSyncing(false), 2000);
  };

  return (
    <div className="p-4 space-y-4 max-w-[1920px] mx-auto font-mono text-xs">
      
      {/* Top Banner */}
      <div className="bg-command-card p-4 rounded-xl border border-command-border flex items-center justify-between">
        <div>
          <h2 className="font-extrabold text-slate-100 text-base uppercase tracking-wider flex items-center gap-2">
            <Cable className="w-5 h-5 text-cyan-400" /> VIDEO MANAGEMENT SYSTEM (VMS) INTEGRATIONS
          </h2>
          <p className="text-xs text-slate-400">
            Real-time bridge to Milestone, Hikvision, Dahua, Axis & ONVIF camera infrastructure
          </p>
        </div>

        <button
          onClick={triggerSync}
          className="px-4 py-2 bg-cyan-500/20 hover:bg-cyan-500/30 border border-cyan-500/40 text-cyan-300 rounded-lg font-bold flex items-center gap-1.5 transition shadow-glow-cyan"
        >
          <RefreshCw className={`w-4 h-4 ${syncing ? 'animate-spin' : ''}`} />
          <span>{syncing ? 'SYNCING VMS CLUSTERS...' : 'SYNC ALL INTEGRATIONS'}</span>
        </button>
      </div>

      {/* VMS Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {VMS_PROVIDERS.map((vms) => (
          <div key={vms.id} className="bg-command-card p-5 rounded-xl border border-command-border space-y-3">
            <div className="flex justify-between items-start border-b border-command-border pb-3">
              <div>
                <h3 className="font-extrabold text-slate-100 text-sm">{vms.name}</h3>
                <span className="text-[10px] text-cyan-400 font-semibold">{vms.type}</span>
              </div>
              <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 text-[10px] font-bold flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" /> {vms.status}
              </span>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between text-slate-400 text-[11px]">
                <span>STREAM ENDPOINT:</span>
                <span className="text-slate-300 truncate max-w-[160px]">{vms.endpoint}</span>
              </div>
              <div className="flex justify-between text-slate-400 text-[11px]">
                <span>CONNECTED CAMERAS:</span>
                <span className="text-slate-100 font-bold">{vms.cameras} units</span>
              </div>
              <div className="flex justify-between text-slate-400 text-[11px]">
                <span>STREAM LATENCY:</span>
                <span className="text-emerald-400 font-bold">{vms.latency}</span>
              </div>
            </div>

            <div className="pt-2 border-t border-command-border flex justify-between items-center text-[10px] text-slate-400">
              <span className="flex items-center gap-1 text-emerald-400">
                <ShieldCheck className="w-3.5 h-3.5" /> 256-BIT SSL ACTIVE
              </span>
              <span>HEARTBEAT: 1s</span>
            </div>
          </div>
        ))}
      </div>

    </div>
  );
}
