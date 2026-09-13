import React from 'react';
import { Video, Car, AlertOctagon, Map, Search, Terminal } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, alertBadgeCount = 3 }) {
  const navItems = [
    { id: 'live-cameras', label: 'LIVE SURVEILLANCE', icon: Video, badge: 'LIVE' },
    { id: 'vehicle-tracking', label: 'ANPR TRACKING', icon: Car, badge: 'HOT' },
    { id: 'alerts', label: 'INCIDENT ALERTS', icon: AlertOctagon, badge: alertBadgeCount ? `${alertBadgeCount}` : null, isAlert: true },
    { id: 'gis', label: 'GIS MAP VIEW', icon: Map, badge: 'GUJARAT' },
    { id: 'event-search', label: 'AI SEARCH & ANALYTICS', icon: Search, badge: 'LOGS' },
  ];

  return (
    <nav className="bg-[#070b16] border-b border-command-border/60 px-4 py-2">
      <div className="max-w-[1920px] mx-auto flex items-center justify-between overflow-x-auto no-scrollbar gap-2">
        <div className="flex items-center gap-1.5 min-w-max">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`relative flex items-center gap-2.5 px-4 py-2 rounded-lg font-mono text-xs font-semibold tracking-wider transition-all duration-200 ${
                  isActive
                    ? 'bg-gradient-to-r from-cyan-950/80 to-blue-950/80 border border-cyan-500/60 text-cyan-300 shadow-glow-cyan'
                    : 'bg-command-card/60 border border-command-border/40 text-slate-400 hover:text-slate-200 hover:border-command-border hover:bg-command-card'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-cyan-400' : 'text-slate-400'}`} />
                <span>{item.label}</span>

                {item.badge && (
                  <span
                    className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                      item.isAlert
                        ? 'bg-rose-500 text-white animate-pulse'
                        : isActive
                        ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                        : 'bg-slate-800 text-slate-400'
                    }`}
                  >
                    {item.badge}
                  </span>
                )}

                {isActive && (
                  <span className="absolute bottom-0 left-3 right-3 h-[2px] bg-cyan-400 rounded-full shadow-[0_0_8px_#00f2fe]" />
                )}
              </button>
            );
          })}
        </div>

        {/* Quick status bar indicator */}
        <div className="hidden xl:flex items-center gap-3 text-xs font-mono text-slate-400 bg-command-card/40 border border-command-border/40 px-3 py-1.5 rounded-lg">
          <span className="flex items-center gap-1.5 text-emerald-400">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
            RTSP STREAM DISPATCHER: ACTIVE
          </span>
        </div>
      </div>
    </nav>
  );
}
