import React, { useState } from 'react';
import { AlertOctagon, ShieldAlert, CheckCircle, Bell, Radio, Volume2, Filter, RefreshCw, Send, Check } from 'lucide-react';

const INITIAL_ALERTS = [
  {
    id: 'ALT-1092',
    timestamp: '09:07:44 IST',
    severity: 'CRITICAL',
    title: 'STOLEN VEHICLE DETECTED (ANPR MATCH)',
    location: 'CAM-001 • SG Highway Iskcon Crossroad',
    details: 'Plate GJ-01-AB-1234 matched stolen vehicle database. Direction: Heading South toward YMCA.',
    status: 'ACTIVE THREAT',
    camera: 'CAM-001',
    pcrUnit: 'PCR-04 (Vastrapur Sector)'
  },
  {
    id: 'ALT-1091',
    timestamp: '09:04:12 IST',
    severity: 'CRITICAL',
    title: 'WRONG-WAY DRIVING HAZARD',
    location: 'CAM-004 • Ahmedabad-Vadodara Express Toll',
    details: 'AI Vision detected heavy truck driving opposite direction at lane 2. Speed: 78 km/h.',
    status: 'ACTIVE THREAT',
    camera: 'CAM-004',
    pcrUnit: 'Highway Patrol PCR-12'
  },
  {
    id: 'ALT-1090',
    timestamp: '08:58:30 IST',
    severity: 'WARNING',
    title: 'OVER-SPEEDING VIOLATION (> 100 KM/H)',
    location: 'CAM-004 • Express Tollway Km 42',
    details: 'Vehicle GJ-05-CD-3321 clocked at 104 km/h in 80 km/h speed limit zone.',
    status: 'ACTIVE THREAT',
    camera: 'CAM-004',
    pcrUnit: 'Automated E-Challan Issued'
  },
  {
    id: 'ALT-1089',
    timestamp: '08:45:00 IST',
    severity: 'INFO',
    title: 'HIGH CROWD DENSITY DETECTED',
    location: 'CAM-002 • Sabarmati Riverfront Promenade',
    details: 'Crowd density threshold exceeded: 120+ persons detected near Event Ground Gate 3.',
    status: 'MONITORING',
    camera: 'CAM-002',
    pcrUnit: 'Riverfront Police Outpost'
  },
  {
    id: 'ALT-1088',
    timestamp: '08:20:15 IST',
    severity: 'WARNING',
    title: 'ANPR UNIDENTIFIED PLATE FORMAT',
    location: 'CAM-005 • Rajkot Trikon Baug',
    details: 'Obscured or damaged vehicle plate number detected on two-wheeler.',
    status: 'RESOLVED',
    camera: 'CAM-005',
    pcrUnit: 'City Patrol Unit 09'
  }
];

export default function Alerts({ isSoundMuted }) {
  const [alerts, setAlerts] = useState(INITIAL_ALERTS);
  const [filterSeverity, setFilterSeverity] = useState('ALL');
  const [dispatchedUnits, setDispatchedUnits] = useState({});

  const playAlertSound = () => {
    if (isSoundMuted) return;
    try {
      const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(880, audioCtx.currentTime); // A5 note
      osc.frequency.exponentialRampToValueAtTime(440, audioCtx.currentTime + 0.3);
      gain.gain.setValueAtTime(0.2, audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.3);
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      osc.start();
      osc.stop(audioCtx.currentTime + 0.3);
    } catch {}
  };

  const markResolved = (id) => {
    setAlerts(prev => prev.map(a => a.id === id ? { ...a, status: 'RESOLVED' } : a));
  };

  const dispatchPcr = (id, pcrUnit) => {
    playAlertSound();
    setDispatchedUnits(prev => ({ ...prev, [id]: pcrUnit }));
  };

  const filteredAlerts = filterSeverity === 'ALL'
    ? alerts
    : alerts.filter(a => a.severity === filterSeverity);

  return (
    <div className="p-4 space-y-4 max-w-[1920px] mx-auto">
      
      {/* Header & Filter Controls */}
      <div className="bg-command-card p-4 rounded-xl border border-command-border flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="font-mono font-extrabold text-slate-100 text-base uppercase tracking-wider flex items-center gap-2">
            <AlertOctagon className="w-5 h-5 text-rose-400 animate-pulse" /> REAL-TIME INCIDENT RESPONSE & EMERGENCY DISPATCH
          </h2>
          <p className="text-xs text-slate-400 font-mono">
            Statewide CCTV AI Threat Alerts • PCR Van Dispatch • Automated Incident Log
          </p>
        </div>

        {/* Severity Filter Tabs */}
        <div className="flex items-center gap-2 font-mono text-xs">
          <span className="text-slate-400 flex items-center gap-1">
            <Filter className="w-3.5 h-3.5 text-cyan-400" /> SEVERITY:
          </span>
          {['ALL', 'CRITICAL', 'WARNING', 'INFO'].map((sev) => (
            <button
              key={sev}
              onClick={() => setFilterSeverity(sev)}
              className={`px-3 py-1 rounded font-bold transition ${
                filterSeverity === sev
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-glow-cyan'
                  : 'bg-command-bg border border-command-border text-slate-400 hover:text-slate-200'
              }`}
            >
              {sev}
            </button>
          ))}
        </div>
      </div>

      {/* Incident Alert Feed */}
      <div className="space-y-3">
        {filteredAlerts.map((alert) => {
          const isCritical = alert.severity === 'CRITICAL';
          const isWarning = alert.severity === 'WARNING';
          const isDispatched = !!dispatchedUnits[alert.id];
          const isResolved = alert.status === 'RESOLVED';

          return (
            <div
              key={alert.id}
              className={`p-4 rounded-xl border font-mono text-xs transition-all duration-200 ${
                isResolved
                  ? 'bg-command-card/50 border-command-border opacity-70'
                  : isCritical
                  ? 'bg-rose-950/30 border-rose-600/70 shadow-glow-alert'
                  : isWarning
                  ? 'bg-amber-950/20 border-amber-500/50'
                  : 'bg-command-card border-command-border'
              }`}
            >
              <div className="flex flex-wrap items-start justify-between gap-3 border-b border-command-border/60 pb-3">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg ${
                    isCritical ? 'bg-rose-500/20 text-rose-400 border border-rose-500/40' :
                    isWarning ? 'bg-amber-500/20 text-amber-400 border border-amber-500/40' :
                    'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                  }`}>
                    <ShieldAlert className="w-5 h-5" />
                  </div>

                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-extrabold text-slate-100 text-sm tracking-wider">{alert.title}</span>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        isCritical ? 'bg-rose-600 text-white' :
                        isWarning ? 'bg-amber-500 text-black' :
                        'bg-cyan-600 text-white'
                      }`}>
                        {alert.severity}
                      </span>
                    </div>
                    <p className="text-cyan-300 text-[11px] mt-0.5">{alert.location}</p>
                  </div>
                </div>

                <div className="text-right">
                  <span className="text-slate-400 text-[11px]">{alert.timestamp}</span>
                  <div className="mt-0.5">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                      isResolved
                        ? 'bg-emerald-950 text-emerald-300 border-emerald-500/40'
                        : 'bg-rose-950 text-rose-300 border-rose-500/40 animate-pulse'
                    }`}>
                      {alert.status}
                    </span>
                  </div>
                </div>
              </div>

              {/* Alert Details Body */}
              <div className="py-3 text-slate-300 text-xs">
                {alert.details}
              </div>

              {/* Action Buttons Footer */}
              <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-command-border/60">
                <div className="flex items-center gap-2 text-[11px] text-slate-400">
                  <span>RECOMMENDED ACTION:</span>
                  <span className="text-slate-200 font-bold">{alert.pcrUnit}</span>
                </div>

                <div className="flex items-center gap-2">
                  {!isResolved && (
                    <>
                      {isDispatched ? (
                        <span className="px-3 py-1.5 rounded bg-emerald-950 border border-emerald-500 text-emerald-300 text-[11px] font-bold flex items-center gap-1.5">
                          <Check className="w-3.5 h-3.5 text-emerald-400" /> DISPATCHED: {dispatchedUnits[alert.id]}
                        </span>
                      ) : (
                        <button
                          onClick={() => dispatchPcr(alert.id, alert.pcrUnit)}
                          className="px-3 py-1.5 rounded bg-rose-600 hover:bg-rose-500 text-white font-bold text-[11px] flex items-center gap-1.5 transition"
                        >
                          <Send className="w-3.5 h-3.5" /> DISPATCH PCR UNIT
                        </button>
                      )}

                      <button
                        onClick={() => markResolved(alert.id)}
                        className="px-3 py-1.5 rounded bg-command-bg border border-command-border hover:border-emerald-500/60 text-slate-300 hover:text-emerald-300 text-[11px] flex items-center gap-1.5 transition"
                      >
                        <CheckCircle className="w-3.5 h-3.5" /> MARK RESOLVED
                      </button>
                    </>
                  )}
                </div>
              </div>

            </div>
          );
        })}
      </div>

    </div>
  );
}
