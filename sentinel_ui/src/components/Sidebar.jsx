import React from 'react';
import { 
  LayoutDashboard, Video, Map as MapIcon, Car, AlertOctagon, ShieldCheck, 
  BarChart3, Search, Database, Cable, Activity, ChevronLeft, ChevronRight, 
  FileText, Shield, Sparkles, Layers
} from 'lucide-react';

export default function Sidebar({ activeTab, setActiveTab, isCollapsed, setIsCollapsed, alertCount = 12 }) {
  const sections = [
    {
      category: 'OPERATIONS',
      items: [
        { id: 'command-center', label: 'COMMAND CENTER', icon: LayoutDashboard },
        { id: 'live-cameras', label: 'LIVE CAMERAS', icon: Video, badge: 'LIVE' },
        { id: 'gis', label: 'CAMERA GIS', icon: MapIcon, badge: 'RADAR' },
        { id: 'vehicle-tracking', label: 'VEHICLE TRACKING', icon: Car },
        { id: 'alerts', label: 'ALERTS CONSOLE', icon: AlertOctagon, badge: alertCount ? `${alertCount}` : null, isAlert: true },
      ]
    },
    {
      category: 'INTELLIGENCE',
      items: [
        { id: 'watchlist', label: 'WATCHLIST REGISTRY', icon: ShieldCheck },
        { id: 'video-analytics', label: 'VIDEO ANALYTICS', icon: BarChart3 },
        { id: 'event-search', label: 'EVENT SEARCH', icon: Search },
      ]
    },
    {
      category: 'SYSTEM MATRIX',
      items: [
        { id: 'camera-registry', label: 'CAMERA REGISTRY', icon: Database },
        { id: 'vms-integrations', label: 'VMS INTEGRATIONS', icon: Cable },
        { id: 'system-health', label: 'SYSTEM HEALTH', icon: Activity },
      ]
    }
  ];

  return (
    <aside 
      className={`bg-[#050814]/95 backdrop-blur-xl border-r border-command-border/90 flex flex-col justify-between transition-all duration-300 z-40 select-none shadow-2xl ${
        isCollapsed ? 'w-16' : 'w-64'
      }`}
    >
      {/* Brand Header */}
      <div>
        <div className="p-3.5 border-b border-command-border/80 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="relative flex items-center justify-center w-9 h-9 rounded-xl bg-gradient-to-br from-cyan-500/20 to-blue-600/40 border border-cyan-500/60 text-cyan-300 shrink-0 shadow-glow-cyan">
              <Shield className="w-5 h-5 text-cyan-400" />
              <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-emerald-400 rounded-full animate-ping" />
              <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-emerald-400 rounded-full" />
            </div>

            {!isCollapsed && (
              <div className="overflow-hidden">
                <div className="flex items-center gap-2">
                  <h1 className="font-mono font-extrabold text-sm tracking-wider text-slate-100">
                    SENTINEL<span className="text-cyan-400">.AI</span>
                  </h1>
                  <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-cyan-950 border border-cyan-500/40 text-cyan-300 font-bold">
                    v3.0
                  </span>
                </div>
                <p className="text-[10px] text-slate-400 font-mono truncate">
                  GUJARAT POLICE C3
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Grouped Navigation */}
        <nav className="p-2 space-y-4 overflow-y-auto max-h-[calc(100vh-170px)] no-scrollbar font-mono">
          {sections.map((sec) => (
            <div key={sec.category} className="space-y-1">
              {!isCollapsed && (
                <div className="px-3 py-1 text-[9px] font-bold text-slate-500 tracking-widest uppercase">
                  {sec.category}
                </div>
              )}

              {sec.items.map((item) => {
                const Icon = item.icon;
                const isActive = activeTab === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => setActiveTab(item.id)}
                    title={isCollapsed ? item.label : undefined}
                    className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-semibold tracking-wide transition-all duration-150 ${
                      isActive
                        ? 'bg-gradient-to-r from-cyan-950/90 to-blue-950/90 border border-cyan-500/70 text-cyan-300 shadow-glow-cyan font-bold'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-command-card/80 border border-transparent'
                    }`}
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-cyan-400 animate-pulse' : 'text-slate-400'}`} />
                      {!isCollapsed && <span className="truncate">{item.label}</span>}
                    </div>

                    {!isCollapsed && item.badge && (
                      <span
                        className={`px-1.5 py-0.2 rounded text-[10px] font-bold ${
                          item.isAlert
                            ? 'bg-rose-500 text-white animate-pulse shadow-glow-alert'
                            : isActive
                            ? 'bg-cyan-500/30 text-cyan-300 border border-cyan-500/40'
                            : 'bg-slate-800 text-slate-400'
                        }`}
                      >
                        {item.badge}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          ))}
        </nav>
      </div>

      {/* Footer Collapse Control */}
      <div className="p-2 border-t border-command-border/80 font-mono text-xs">
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="w-full py-2 px-3 rounded-xl bg-command-bg/60 hover:bg-command-card text-slate-400 hover:text-slate-200 flex items-center justify-center gap-2 border border-command-border/60 transition"
        >
          {isCollapsed ? (
            <ChevronRight className="w-4 h-4 text-cyan-400" />
          ) : (
            <>
              <ChevronLeft className="w-4 h-4 text-cyan-400" />
              <span className="text-[11px] font-bold">COLLAPSE DOCK</span>
            </>
          )}
        </button>
      </div>
    </aside>
  );
}
