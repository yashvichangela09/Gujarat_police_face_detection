import React, { useState, useEffect } from 'react';
import { Shield, Bell, User, Volume2, VolumeX, Activity, Bot, Radio, Zap, ShieldAlert, Terminal } from 'lucide-react';

export default function Header({ activeTab, isSoundMuted, setIsSoundMuted, alertCount = 12, onToggleCopilot, isCopilotOpen }) {
  const [timeStr, setTimeStr] = useState('');
  const [dateStr, setDateStr] = useState('');

  useEffect(() => {
    const timer = setInterval(() => {
      const now = new Date();
      setTimeStr(now.toLocaleTimeString('en-US', { hour12: false }));
      setDateStr(now.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }));
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const tabTitles = {
    'command-center': 'COMMAND CENTER',
    'live-cameras': 'LIVE CAMERAS',
    'gis': 'CAMERA GIS',
    'vehicle-tracking': 'VEHICLE TRACKING',
    'alerts': 'ALERTS CONSOLE',
    'watchlist': 'WATCHLIST REGISTRY',
    'video-analytics': 'VIDEO ANALYTICS',
    'event-search': 'EVENT SEARCH',
    'camera-registry': 'CAMERA REGISTRY',
    'vms-integrations': 'VMS INTEGRATIONS',
    'system-health': 'SYSTEM HEALTH',
  };

  return (
    <header className="bg-[#050914]/90 backdrop-blur-md border-b border-command-border px-5 py-2.5 flex items-center justify-between gap-4 font-mono text-xs z-30 sticky top-0">
      
      {/* Left: Breadcrumb & Title */}
      <div className="flex items-center gap-4">
        <div>
          <div className="text-[10px] text-slate-500 uppercase tracking-widest flex items-center gap-1.5">
            <span>HQ COMMAND</span>
            <span>/</span>
            <span className="text-cyan-400 font-bold">{activeTab.replace('-', ' ')}</span>
          </div>
          <h2 className="font-extrabold text-slate-100 text-sm tracking-wider uppercase mt-0.5">
            {tabTitles[activeTab] || 'TACTICAL COMMAND'}
          </h2>
        </div>
      </div>

      {/* Center: DEFCON Threat Dial & Live System Operational Ticker */}
      <div className="hidden lg:flex items-center gap-4">
        
        {/* DEFCON Threat Dial Indicator */}
        <div className="flex items-center gap-2.5 bg-rose-950/40 border border-rose-600/50 px-3.5 py-1.5 rounded-xl shadow-glow-alert">
          <div className="relative flex items-center justify-center w-5 h-5">
            <span className="w-4 h-4 rounded-full border-2 border-rose-500 border-t-transparent animate-spin" />
            <span className="absolute w-1.5 h-1.5 bg-rose-400 rounded-full animate-ping" />
          </div>
          <div>
            <div className="text-[9px] text-rose-300 font-bold tracking-widest">THREAT MATRIX: BRAVO</div>
            <div className="text-[11px] text-rose-400 font-extrabold leading-none">HEIGHTENED PERIMETER</div>
          </div>
        </div>

        {/* Live PCR Fleet Telemetry */}
        <div className="bg-command-card/90 px-3.5 py-1.5 rounded-xl border border-command-border flex items-center gap-2 text-slate-300">
          <Radio className="w-4 h-4 text-cyan-400 animate-pulse" />
          <div>
            <div className="text-[9px] text-slate-400">ACTIVE PATROLS</div>
            <div className="text-[11px] text-cyan-300 font-bold leading-none">24 PCR UNITS DISPATCHED</div>
          </div>
        </div>

        {/* Live IST Clock */}
        <div className="bg-command-card/90 px-3.5 py-1.5 rounded-xl border border-command-border text-slate-300">
          <div className="text-[9px] text-slate-400">STATE CLOCK (IST)</div>
          <div className="text-[11px] text-slate-100 font-extrabold leading-none">
            {dateStr || '10 Sep 2026'} | <span className="text-cyan-400">{timeStr || '09:42:00'}</span>
          </div>
        </div>

      </div>

      {/* Right: AI Copilot Trigger, Audio Synth & Profile */}
      <div className="flex items-center gap-3">
        
        {/* Sentinel AI Copilot Toggle Button */}
        <button
          onClick={onToggleCopilot}
          className={`px-3 py-1.5 rounded-xl font-bold flex items-center gap-2 transition text-xs ${
            isCopilotOpen
              ? 'bg-cyan-500 text-black shadow-glow-cyan font-extrabold'
              : 'bg-cyan-950/60 border border-cyan-500/60 text-cyan-300 hover:bg-cyan-900/60 shadow-inner'
          }`}
        >
          <Bot className={`w-4 h-4 ${isCopilotOpen ? 'animate-bounce' : 'animate-pulse'}`} />
          <span className="hidden sm:inline">AI COPILOT</span>
        </button>

        {/* Audio Alert Synth Toggle */}
        <button
          onClick={() => setIsSoundMuted(!isSoundMuted)}
          className={`p-2 rounded-xl border text-xs font-mono transition flex items-center gap-1.5 ${
            isSoundMuted 
              ? 'bg-rose-950/40 border-rose-700/50 text-rose-400' 
              : 'bg-command-card border-command-border text-cyan-400 hover:border-cyan-500'
          }`}
          title={isSoundMuted ? 'Unmute tactical audio' : 'Mute tactical audio'}
        >
          {isSoundMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
        </button>

        {/* Alert Notifications */}
        <div className="relative p-2 rounded-xl bg-command-card border border-command-border text-slate-300 cursor-pointer hover:border-cyan-500">
          <Bell className="w-4 h-4" />
          {alertCount > 0 && (
            <span className="absolute -top-1 -right-1 px-1.5 py-0.2 rounded-full bg-rose-500 text-white font-bold text-[9px] animate-pulse">
              {alertCount}
            </span>
          )}
        </div>

        {/* Senior Duty Officer Badge */}
        <div className="flex items-center gap-2.5 bg-command-card px-3 py-1.5 rounded-xl border border-command-border">
          <div className="w-7 h-7 rounded-lg bg-cyan-950 border border-cyan-500/40 flex items-center justify-center text-cyan-400">
            <User className="w-4 h-4" />
          </div>
          <div className="text-left hidden xl:block">
            <div className="text-slate-100 font-bold text-[11px] leading-tight">
              Command Operator <span className="text-slate-400 font-normal">[GP-CTRL-094]</span>
            </div>
            <div className="text-[10px] text-cyan-400 font-medium">
              Senior Duty Officer • C3 Grid
            </div>
          </div>
        </div>

      </div>

    </header>
  );
}
