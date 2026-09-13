import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import AiCopilot from './components/AiCopilot';
import CommandCenter from './components/CommandCenter';
import LiveCameras from './components/LiveCameras';
import GisMap from './components/GisMap';
import VehicleTracking from './components/VehicleTracking';
import Alerts from './components/Alerts';
import WatchlistRegistry from './components/WatchlistRegistry';
import VideoAnalytics from './components/VideoAnalytics';
import EventSearch from './components/EventSearch';
import CameraRegistry from './components/CameraRegistry';
import VmsIntegrations from './components/VmsIntegrations';
import SystemHealth from './components/SystemHealth';

export default function App() {
  const [activeTab, setActiveTab] = useState('command-center');
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isSoundMuted, setIsSoundMuted] = useState(false);
  const [alertCount, setAlertCount] = useState(12);
  const [isCopilotOpen, setIsCopilotOpen] = useState(false);

  const handleSelectCameraFromMap = (cam) => {
    setActiveTab('live-cameras');
  };

  return (
    <div className="min-h-screen bg-[#030712] text-slate-100 flex overflow-x-hidden selection:bg-cyan-500 selection:text-black">
      
      {/* Floating Tactical Dock Navigation */}
      <Sidebar 
        activeTab={activeTab} 
        setActiveTab={setActiveTab} 
        isCollapsed={isCollapsed} 
        setIsCollapsed={setIsCollapsed} 
        alertCount={alertCount}
      />

      {/* Main Tactical Command Canvas */}
      <div className="flex-1 flex flex-col min-w-0 bg-tactical-hex-bg">
        
        {/* Master Tactical HUD Header */}
        <Header 
          activeTab={activeTab} 
          isSoundMuted={isSoundMuted} 
          setIsSoundMuted={setIsSoundMuted} 
          alertCount={alertCount}
          onToggleCopilot={() => setIsCopilotOpen(!isCopilotOpen)}
          isCopilotOpen={isCopilotOpen}
        />

        {/* Dynamic Screen View */}
        <main className="flex-1 pb-6 overflow-y-auto">
          {activeTab === 'command-center' && <CommandCenter onNavigate={setActiveTab} />}
          {activeTab === 'live-cameras' && <LiveCameras />}
          {activeTab === 'gis' && <GisMap onSelectCamera={handleSelectCameraFromMap} />}
          {activeTab === 'vehicle-tracking' && <VehicleTracking />}
          {activeTab === 'alerts' && <Alerts isSoundMuted={isSoundMuted} />}
          {activeTab === 'watchlist' && <WatchlistRegistry />}
          {activeTab === 'video-analytics' && <VideoAnalytics />}
          {activeTab === 'event-search' && <EventSearch />}
          {activeTab === 'camera-registry' && <CameraRegistry />}
          {activeTab === 'vms-integrations' && <VmsIntegrations />}
          {activeTab === 'system-health' && <SystemHealth />}
        </main>

        {/* Sentinel AI Copilot Assistant Drawer */}
        <AiCopilot 
          isOpen={isCopilotOpen} 
          onClose={() => setIsCopilotOpen(false)}
          onActionTrigger={(action) => console.log('Copilot action:', action)}
        />

        {/* Tactical Footer Telemetry Bar */}
        <footer className="bg-[#030610] border-t border-command-border/80 py-2 px-5 font-mono text-[11px] text-slate-400 flex flex-wrap items-center justify-between gap-2 z-20">
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1.5 text-emerald-400 font-bold">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
              SENTINEL AI v3.0 PRO
            </span>
            <span className="text-slate-600">•</span>
            <span>GUJARAT POLICE C3 TACTICAL GRID</span>
          </div>

          <div className="flex items-center gap-4 text-slate-400 text-[10px]">
            <span>YOLOv11: 8100 (ONLINE)</span>
            <span>•</span>
            <span>ENCRYPTION: QUANTUM-RESISTANT 512-BIT</span>
            <span>•</span>
            <button
              onClick={() => setIsCopilotOpen(true)}
              className="text-cyan-400 hover:underline font-bold"
            >
              [OPEN COPILOT PROMPT]
            </button>
          </div>
        </footer>

      </div>

    </div>
  );
}
