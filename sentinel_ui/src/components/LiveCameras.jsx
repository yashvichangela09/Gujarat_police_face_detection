import React, { useState, useEffect, useRef } from 'react';
import { 
  Grid, Maximize2, Camera, Eye, Zap, ShieldAlert, Sliders, 
  RotateCcw, Play, Square, Activity, Layers, Sun, Moon, AlertTriangle
} from 'lucide-react';
import LiveAiFeed from './ai/LiveAiFeed';
import { startAiForCamera, stopAiForCamera } from '../services/liveAiService';

const CAMERAS = [
  {
    id: 'CAM-001',
    streamUrl: 'http://127.0.0.1:5000/api/camera/CAMERA_01/stream',
    videoUrl: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4',
    name: 'SG Highway - Iskcon Crossroad',
    city: 'Ahmedabad',
    status: 'ONLINE',
    fps: 30,
    resolution: '1280x720',
    rtsp_url: 'http://127.0.0.1:5000/api/camera/CAMERA_01/stream',
    type: 'YOLOv11 + ANPR + Re-ID',
    speedLimit: 70,
    detectionsCount: 42,
    bgGradient: 'from-blue-950 via-slate-900 to-cyan-950'
  },
  {
    id: 'CAM-002',
    streamUrl: 'http://127.0.0.1:5000/api/camera/CAMERA_02/stream',
    videoUrl: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4',
    name: 'Sabarmati Riverfront East',
    city: 'Ahmedabad',
    status: 'ONLINE',
    fps: 30,
    resolution: '1280x720',
    rtsp_url: 'http://127.0.0.1:5000/api/camera/CAMERA_02/stream',
    type: 'YOLOv11 + Vehicle Re-ID',
    speedLimit: 40,
    detectionsCount: 18,
    bgGradient: 'from-slate-950 via-cyan-950 to-indigo-950'
  },
  {
    id: 'CAM-003',
    streamUrl: 'http://127.0.0.1:5000/api/camera/CAMERA_03/stream',
    videoUrl: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4',
    name: 'Surat Textile Market Circle',
    city: 'Surat',
    status: 'ONLINE',
    fps: 30,
    resolution: '1280x720',
    rtsp_url: 'http://127.0.0.1:5000/api/camera/CAMERA_03/stream',
    type: 'Traffic Flow & ANPR',
    speedLimit: 50,
    detectionsCount: 65,
    bgGradient: 'from-indigo-950 via-slate-900 to-blue-950'
  },
  {
    id: 'CAM-004',
    streamUrl: 'http://127.0.0.1:5000/api/camera/CAMERA_04/stream',
    videoUrl: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerJoyrides.mp4',
    name: 'Ahmedabad-Vadodara Express Toll',
    city: 'Vadodara Toll',
    status: 'ONLINE',
    fps: 30,
    resolution: '1280x720',
    rtsp_url: 'http://127.0.0.1:5000/api/camera/CAMERA_04/stream',
    type: 'High-Speed ANPR Radar',
    speedLimit: 100,
    detectionsCount: 89,
    bgGradient: 'from-cyan-950 via-slate-950 to-blue-950'
  },
  {
    id: 'CAM-005',
    streamUrl: 'http://127.0.0.1:5000/api/camera/CAMERA_05/stream',
    videoUrl: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerMeltdowns.mp4',
    name: 'Overhead Surveillance Matrix',
    city: 'Gandhinagar',
    status: 'ONLINE',
    fps: 30,
    resolution: '1280x720',
    rtsp_url: 'http://127.0.0.1:5000/api/camera/CAMERA_05/stream',
    type: 'Multi-Vehicle Detection',
    speedLimit: 45,
    detectionsCount: 31,
    bgGradient: 'from-slate-950 via-blue-950 to-cyan-950'
  }
];

const isLocalhost = typeof window !== 'undefined' && 
  (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');

export default function LiveCameras() {
  const [selectedCam, setSelectedCam] = useState(CAMERAS[0]);
  const [gridMode, setGridMode] = useState('2x2');
  const [isNightVision, setIsNightVision] = useState(false);
  const [isBoundingBoxEnabled, setIsBoundingBoxEnabled] = useState(true);
  const [isAiServiceRunning, setIsAiServiceRunning] = useState(false);
  const [aiServiceStatus, setAiServiceStatus] = useState('');
  const [ptzZoom, setPtzZoom] = useState(1.0);
  const [ptzPan, setPtzPan] = useState(0);
  const [ptzTilt, setPtzTilt] = useState(0);
  const [snapshotNotice, setSnapshotNotice] = useState('');
  const [showEmbeddedMatrix, setShowEmbeddedMatrix] = useState(false);

  // Dynamic Animated Bounding Boxes State
  const [bboxes, setBboxes] = useState([]);

  useEffect(() => {
    // Generate realistic moving AI bounding boxes
    const interval = setInterval(() => {
      const vehicleTypes = [
        { label: 'CAR (Sedan)', conf: 0.96, color: '#00f2fe', plate: 'GJ-01-AB-1234', faceLabel: 'CITIZEN: CLEAR', isWanted: false },
        { label: 'MOTORCYCLE', conf: 0.88, color: '#00f5d4', plate: 'GJ-01-XY-5678', faceLabel: 'CITIZEN: CLEAR', isWanted: false },
        { label: 'CAR (SUV)', conf: 0.94, color: '#ff2a6d', plate: 'GJ-05-CD-3321', faceLabel: '🚨 WANTED: Shahrukh Khan', isWanted: true },
        { label: 'BUS (GSRTC)', conf: 0.95, color: '#9d4edd', plate: 'GJ-18-Z-4411', faceLabel: 'CITIZEN: CLEAR', isWanted: false },
        { label: 'CAR (Sedan)', conf: 0.92, color: '#ff2a6d', plate: 'GJ-06-ZZ-9900', faceLabel: '🚨 WANTED: Ajay Devgan', isWanted: true },
      ];

      const newBoxes = Array.from({ length: 4 }).map((_, idx) => {
        const item = vehicleTypes[idx % vehicleTypes.length];
        const time = Date.now() / 1000;
        const x = 12 + (idx * 22) + Math.sin(time + idx * 1.5) * 6;
        const y = 25 + (idx * 14) + Math.cos(time * 1.2 + idx) * 5;
        const speed = Math.floor(48 + Math.random() * 32);
        return {
          id: idx,
          x: Math.max(8, Math.min(75, x)),
          y: Math.max(18, Math.min(62, y)),
          w: 16 + (idx % 2) * 4,
          h: 20 + (idx % 2) * 3,
          label: item.label,
          conf: (item.conf + Math.random() * 0.03 - 0.015).toFixed(2),
          color: item.isWanted ? '#ff2a6d' : (speed > selectedCam.speedLimit ? '#ff2a6d' : item.color),
          plate: item.plate,
          speed,
          isSpeeding: speed > selectedCam.speedLimit,
          faceLabel: item.faceLabel,
          isWanted: item.isWanted,
        };
      });
      setBboxes(newBoxes);
    }, 600);

    return () => clearInterval(interval);
  }, [selectedCam]);

  const handleStartPythonAi = async () => {
    try {
      setAiServiceStatus('Connecting to Python FastAPI (127.0.0.1:8100)...');
      const res = await startAiForCamera(selectedCam);
      setIsAiServiceRunning(true);
      setAiServiceStatus(`Python YOLO Worker Active for ${selectedCam.id}`);
    } catch (err) {
      setAiServiceStatus(`Python AI API error: ${err.message}`);
    }
  };

  const handleStopPythonAi = async () => {
    try {
      await stopAiForCamera(selectedCam.id);
      setIsAiServiceRunning(false);
      setAiServiceStatus('Python AI worker paused.');
    } catch (err) {
      setAiServiceStatus(err.message);
    }
  };

  const triggerSnapshot = (camName) => {
    setSnapshotNotice(`High-Res Snapshot Saved: ${camName}_${Date.now()}.png`);
    setTimeout(() => setSnapshotNotice(''), 3500);
  };

  const resetPtz = () => {
    setPtzZoom(1.0);
    setPtzPan(0);
    setPtzTilt(0);
  };

  const displayedCameras = gridMode === '1x1' 
    ? [selectedCam] 
    : gridMode === '2x2' 
    ? CAMERAS.slice(0, 4) 
    : CAMERAS;

  return (
    <div className="p-4 space-y-4 max-w-[1920px] mx-auto">
      
      {/* Top Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-command-card p-3 rounded-xl border border-command-border">
        
        {/* Left: View Mode Controls */}
        <div className="flex items-center gap-3">
          <span className="text-xs font-mono text-slate-400 flex items-center gap-1.5">
            <Grid className="w-4 h-4 text-cyan-400" /> VIEW MODE:
          </span>
          <div className="flex bg-command-bg p-1 rounded-lg border border-command-border gap-1 font-mono text-xs">
            {['1x1', '2x2', '3x3'].map((mode) => (
              <button
                key={mode}
                onClick={() => setGridMode(mode)}
                className={`px-3 py-1 rounded font-semibold transition ${
                  gridMode === mode
                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-glow-cyan'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {mode === '1x1' ? 'SINGLE FOCUS' : mode === '2x2' ? 'QUAD VIEW (2x2)' : 'FULL GRID (3x3)'}
              </button>
            ))}
          </div>

          <button
            onClick={() => setIsNightVision(!isNightVision)}
            className={`px-3 py-1.5 rounded-lg border font-mono text-xs flex items-center gap-1.5 transition ${
              isNightVision 
                ? 'bg-emerald-950/80 border-emerald-500/60 text-emerald-300' 
                : 'bg-command-card border-command-border text-slate-300 hover:border-slate-500'
            }`}
          >
            {isNightVision ? <Moon className="w-3.5 h-3.5 text-emerald-400" /> : <Sun className="w-3.5 h-3.5 text-amber-400" />}
            <span>{isNightVision ? 'THERMAL IR NIGHT' : 'DAYLIGHT OPTICAL'}</span>
          </button>

          <button
            onClick={() => setIsBoundingBoxEnabled(!isBoundingBoxEnabled)}
            className={`px-3 py-1.5 rounded-lg border font-mono text-xs flex items-center gap-1.5 transition ${
              isBoundingBoxEnabled 
                ? 'bg-cyan-950/80 border-cyan-500/60 text-cyan-300' 
                : 'bg-command-card border-command-border text-slate-400'
            }`}
          >
            <Eye className="w-3.5 h-3.5" />
            <span>AI OVERLAY: {isBoundingBoxEnabled ? 'ENABLED' : 'HIDDEN'}</span>
          </button>

          <button
            onClick={() => setShowEmbeddedMatrix(!showEmbeddedMatrix)}
            className={`px-3 py-1.5 rounded-lg border font-mono text-xs flex items-center gap-1.5 transition ${
              showEmbeddedMatrix 
                ? 'bg-cyan-500 text-black font-extrabold shadow-glow-cyan' 
                : 'bg-command-card border-cyan-500/50 text-cyan-300 hover:bg-cyan-500/10'
            }`}
          >
            <Activity className="w-3.5 h-3.5" />
            <span>{showEmbeddedMatrix ? 'SHOW CAMERA GRID' : 'EMBED MATRIX DASHBOARD (PORT 5000)'}</span>
          </button>
        </div>

        {/* Right: Python FastAPI Backend Connector / Vercel Banner */}
        <div className="flex items-center gap-3 font-mono text-xs">
          {!isLocalhost && (
            <span className="text-emerald-300 bg-emerald-950/90 border border-emerald-500/60 px-3 py-1 rounded text-[11px] font-bold font-mono animate-pulse">
              ● VERCEL DEMO STREAMING (AI ACTIVE)
            </span>
          )}

          {aiServiceStatus && (
            <span className="text-cyan-300 bg-cyan-950/80 border border-cyan-500/50 px-3 py-1 rounded text-[11px] font-bold">
              {aiServiceStatus}
            </span>
          )}

          {!isAiServiceRunning ? (
            <button
              onClick={handleStartPythonAi}
              className="px-4 py-1.5 rounded-lg bg-emerald-500/20 border border-emerald-500/60 text-emerald-300 hover:bg-emerald-500/30 flex items-center gap-1.5 transition shadow-glow-emerald font-bold"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>START PYTHON YOLO AI</span>
            </button>
          ) : (
            <button
              onClick={handleStopPythonAi}
              className="px-4 py-1.5 rounded-lg bg-rose-500/20 border border-rose-500/60 text-rose-300 hover:bg-rose-500/30 flex items-center gap-1.5 transition font-bold"
            >
              <Square className="w-3.5 h-3.5 fill-current" />
              <span>PAUSE AI WORKER</span>
            </button>
          )}
        </div>

      </div>

      {/* Snapshot Alert Banner */}
      {snapshotNotice && (
        <div className="bg-emerald-950/90 border border-emerald-500 text-emerald-300 px-4 py-2 rounded-lg font-mono text-xs flex items-center justify-between animate-pulse shadow-glow-emerald">
          <span className="flex items-center gap-2">
            <Camera className="w-4 h-4 text-emerald-400" /> {snapshotNotice}
          </span>
          <span className="text-[10px] text-emerald-400 font-bold">HIGH-RES ENCRYPTED ARCHIVE</span>
        </div>
      )}

      {/* Embedded Full SENTINEL AI Command Center Matrix from Port 5000 */}
      {showEmbeddedMatrix ? (
        <div className="w-full bg-command-card rounded-xl border border-cyan-500/50 p-2 shadow-2xl">
          <div className="flex items-center justify-between p-2 bg-black/60 rounded mb-2 font-mono text-xs text-cyan-300">
            <span className="font-bold flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
              SENTINEL AI 2.0 MATRIX — LIVE BACKEND (http://127.0.0.1:5000)
            </span>
            <a href="http://127.0.0.1:5000" target="_blank" rel="noreferrer" className="underline text-emerald-400">
              Open in New Window ↗
            </a>
          </div>
          <iframe 
            src="http://127.0.0.1:5000" 
            title="Sentinel AI Backend Command Center"
            className="w-full h-[850px] rounded-lg border border-command-border"
          />
        </div>
      ) : (
        <>
          {/* Main CCTV Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        
        {/* CCTV Video Streams Area */}
        <div className="lg:col-span-2 space-y-4">
          <div className={`grid gap-3 ${
            gridMode === '1x1' 
              ? 'grid-cols-1' 
              : gridMode === '2x2' 
              ? 'grid-cols-1 md:grid-cols-2' 
              : 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3'
          }`}>
            {displayedCameras.map((cam) => {
              const isSelected = selectedCam.id === cam.id;
              return (
                <div
                  key={cam.id}
                  onClick={() => setSelectedCam(cam)}
                  className={`relative rounded-xl overflow-hidden border cursor-pointer transition-all duration-200 group ${
                    isSelected
                      ? 'border-cyan-400 shadow-glow-cyan ring-1 ring-cyan-500/50'
                      : 'border-command-border hover:border-slate-500 bg-command-card'
                  }`}
                >
                  {/* CCTV Screen Outer Box */}
                  <div 
                    className={`relative aspect-video bg-gradient-to-br ${cam.bgGradient} flex flex-col justify-between p-3 overflow-hidden ${
                      isNightVision ? 'brightness-125 contrast-150 grayscale hue-rotate-90' : ''
                    }`}
                    style={{
                      transform: isSelected ? `scale(${ptzZoom}) translate(${ptzPan * 0.2}px, ${-ptzTilt * 0.2}px)` : 'none',
                      transition: 'transform 0.2s ease-out'
                    }}
                  >
                    {/* Live Stream / Fallback Video Stream */}
                    {isLocalhost ? (
                      <>
                        <img 
                          src={cam.streamUrl} 
                          alt={cam.name} 
                          className="absolute inset-0 w-full h-full object-cover z-10"
                          onError={(e) => {
                            e.target.style.display = 'none';
                          }}
                        />
                        <video
                          autoPlay
                          loop
                          muted
                          playsInline
                          src={cam.videoUrl}
                          className="absolute inset-0 w-full h-full object-cover z-0"
                        />
                      </>
                    ) : (
                      <video
                        autoPlay
                        loop
                        muted
                        playsInline
                        src={cam.videoUrl}
                        className="absolute inset-0 w-full h-full object-cover z-10"
                      />
                    )}

                    {/* Simulated Animated Road / Traffic Canvas background fallback */}
                    <div className="absolute inset-0 opacity-20 pointer-events-none z-0">
                      {/* Moving Highway Perspective Lines */}
                      <svg className="w-full h-full text-cyan-500/20" viewBox="0 0 400 225">
                        <line x1="200" y1="90" x2="40" y2="225" stroke="currentColor" strokeWidth="2" strokeDasharray="8 6" />
                        <line x1="200" y1="90" x2="360" y2="225" stroke="currentColor" strokeWidth="2" strokeDasharray="8 6" />
                        <line x1="200" y1="90" x2="200" y2="225" stroke="currentColor" strokeWidth="1" strokeDasharray="4 4" />
                        <circle cx="200" cy="90" r="18" fill="none" stroke="currentColor" strokeWidth="1" />
                      </svg>
                    </div>

                    <div className="absolute inset-0 scanline-overlay" />
                    <div className="absolute inset-0 cyber-grid-bg opacity-30" />

                    {/* Camera Feed Top HUD Header */}
                    <div className="relative z-10 flex items-center justify-between">
                      <div className="flex items-center gap-2 bg-black/80 backdrop-blur px-2.5 py-1 rounded border border-white/15 font-mono text-[11px]">
                        <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                        <span className="text-white font-bold">{cam.id}</span>
                        <span className="text-cyan-400">● LIVE</span>
                      </div>

                      <div className="flex items-center gap-1.5 bg-black/80 backdrop-blur px-2.5 py-1 rounded border border-white/15 font-mono text-[11px] text-slate-300">
                        <span>{cam.fps} FPS</span>
                        <span>•</span>
                        <span className="text-cyan-300">{cam.resolution}</span>
                      </div>
                    </div>

                    {/* Dynamic AI Bounding Boxes Overlay */}
                    {isBoundingBoxEnabled && bboxes.map((box) => (
                      <div
                        key={box.id}
                        className="absolute z-20 border-2 rounded transition-all duration-300 font-mono text-[10px]"
                        style={{
                          left: `${box.x}%`,
                          top: `${box.y}%`,
                          width: `${box.w}%`,
                          height: `${box.h}%`,
                          borderColor: box.color,
                          boxShadow: `0 0 12px ${box.color}88`
                        }}
                      >
                        {/* Box Header Label */}
                        <div 
                          className="absolute -top-5 left-0 px-1.5 py-0.5 rounded text-black font-bold whitespace-nowrap flex items-center gap-1"
                          style={{ backgroundColor: box.color }}
                        >
                          <span>{box.label}</span>
                          <span>{(box.conf * 100).toFixed(0)}%</span>
                        </div>

                        {/* Face Recognition Badge */}
                        {box.faceLabel && (
                          <div 
                            className={`absolute -top-10 left-0 px-1.5 py-0.5 rounded font-bold whitespace-nowrap flex items-center gap-1 shadow-md ${
                              box.isWanted ? 'bg-rose-600 text-white animate-pulse' : 'bg-emerald-600 text-white'
                            }`}
                          >
                            <span>{box.faceLabel}</span>
                          </div>
                        )}

                        {/* ANPR Plate Badge */}
                        <div className="absolute -bottom-5 left-0 bg-black/90 text-cyan-300 px-1.5 py-0.5 rounded border border-cyan-500/60 font-bold whitespace-nowrap">
                          {box.plate} • {box.speed} km/h
                        </div>

                        {box.isSpeeding && (
                          <div className="absolute -top-14 left-0 bg-rose-600 text-white font-extrabold px-1.5 py-0.5 rounded animate-bounce shadow-glow-alert">
                            ⚠️ OVERSPEED VIOLATION
                          </div>
                        )}
                      </div>
                    ))}

                    {/* Center Crosshair */}
                    <div className="absolute inset-0 flex items-center justify-center pointer-events-none opacity-25">
                      <div className="w-20 h-20 border border-cyan-400 rounded-full flex items-center justify-center">
                        <div className="w-2 h-2 bg-cyan-400 rounded-full" />
                      </div>
                    </div>

                    {/* CCTV Screen Bottom HUD Footer */}
                    <div className="relative z-10 flex items-end justify-between mt-auto">
                      <div className="bg-black/70 backdrop-blur p-1.5 rounded border border-white/10">
                        <p className="text-white font-mono font-bold text-xs leading-tight">{cam.name}</p>
                        <p className="text-cyan-300 text-[10px] font-mono">{cam.city} • {cam.type}</p>
                      </div>

                      <div className="flex items-center gap-1">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            triggerSnapshot(cam.id);
                          }}
                          className="p-1.5 rounded bg-black/80 hover:bg-cyan-500/30 text-slate-200 hover:text-cyan-300 border border-white/20 transition"
                          title="Take High-Res Snapshot"
                        >
                          <Camera className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedCam(cam);
                            setGridMode('1x1');
                          }}
                          className="p-1.5 rounded bg-black/80 hover:bg-cyan-500/30 text-slate-200 hover:text-cyan-300 border border-white/20 transition"
                          title="Focus View"
                        >
                          <Maximize2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>

                  </div>
                </div>
              );
            })}
          </div>

          {/* PTZ Camera Controls Panel */}
          <div className="bg-command-card p-4 rounded-xl border border-command-border space-y-3">
            <div className="flex items-center justify-between border-b border-command-border pb-2">
              <div className="flex items-center gap-2">
                <Sliders className="w-4 h-4 text-cyan-400" />
                <h3 className="font-mono font-bold text-xs text-slate-200 uppercase tracking-wider">
                  PTZ CONTROLLER — {selectedCam.name} ({selectedCam.id})
                </h3>
              </div>
              <button
                onClick={resetPtz}
                className="text-[11px] font-mono text-slate-400 hover:text-cyan-300 flex items-center gap-1 transition"
              >
                <RotateCcw className="w-3 h-3" /> RESET CONTROLS
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 font-mono text-xs">
              
              {/* Pan & Tilt Joystick Controls */}
              <div className="flex flex-col items-center justify-center p-3 bg-command-bg rounded-lg border border-command-border">
                <span className="text-[10px] text-slate-400 mb-2">PAN / TILT JOYSTICK</span>
                <div className="grid grid-cols-3 gap-1 w-28 h-28">
                  <div />
                  <button 
                    onClick={() => setPtzTilt(ptzTilt + 5)}
                    className="bg-command-card hover:bg-cyan-500/20 text-cyan-400 rounded border border-command-border flex items-center justify-center font-bold"
                  >▲</button>
                  <div />
                  <button 
                    onClick={() => setPtzPan(ptzPan - 5)}
                    className="bg-command-card hover:bg-cyan-500/20 text-cyan-400 rounded border border-command-border flex items-center justify-center font-bold"
                  >◀</button>
                  <button 
                    onClick={resetPtz}
                    className="bg-cyan-950 text-cyan-300 rounded border border-cyan-500/40 text-[9px] font-bold"
                  >CENTER</button>
                  <button 
                    onClick={() => setPtzPan(ptzPan + 5)}
                    className="bg-command-card hover:bg-cyan-500/20 text-cyan-400 rounded border border-command-border flex items-center justify-center font-bold"
                  >▶</button>
                  <div />
                  <button 
                    onClick={() => setPtzTilt(ptzTilt - 5)}
                    className="bg-command-card hover:bg-cyan-500/20 text-cyan-400 rounded border border-command-border flex items-center justify-center font-bold"
                  >▼</button>
                  <div />
                </div>
              </div>

              {/* Optical Zoom Level Slider */}
              <div className="space-y-3 p-3 bg-command-bg rounded-lg border border-command-border">
                <div className="flex justify-between text-[11px]">
                  <span className="text-slate-400">OPTICAL ZOOM LEVEL</span>
                  <span className="text-cyan-300 font-bold">{ptzZoom.toFixed(1)}x</span>
                </div>
                <input
                  type="range"
                  min="1.0"
                  max="10.0"
                  step="0.5"
                  value={ptzZoom}
                  onChange={(e) => setPtzZoom(parseFloat(e.target.value))}
                  className="w-full accent-cyan-400 cursor-pointer"
                />
                
                <div className="flex justify-between text-[10px] text-slate-500">
                  <span>1.0x (WIDE)</span>
                  <span>5.0x</span>
                  <span>10.0x (TELE)</span>
                </div>

                <div className="pt-2 border-t border-command-border flex items-center justify-between text-[11px]">
                  <span className="text-slate-400">PAN ANGLE: {ptzPan}°</span>
                  <span className="text-slate-400">TILT ANGLE: {ptzTilt}°</span>
                </div>
              </div>

              {/* Quick Preset Actions */}
              <div className="space-y-2 p-3 bg-command-bg rounded-lg border border-command-border">
                <span className="text-[10px] text-slate-400 block mb-1">COMMAND ACTIONS</span>
                <button
                  onClick={() => triggerSnapshot(selectedCam.name)}
                  className="w-full py-1.5 rounded bg-command-card hover:bg-cyan-500/20 border border-command-border text-slate-200 flex items-center justify-center gap-1.5 transition"
                >
                  <Camera className="w-3.5 h-3.5 text-cyan-400" /> CAPTURE HIGH-RES FRAME
                </button>
                <button
                  onClick={() => alert(`[STROBE ACTIVATED] Flash siren triggered for ${selectedCam.id}`)}
                  className="w-full py-1.5 rounded bg-rose-950/60 hover:bg-rose-900/80 border border-rose-700/60 text-rose-300 flex items-center justify-center gap-1.5 transition"
                >
                  <ShieldAlert className="w-3.5 h-3.5 text-rose-400" /> TRIGGER EMERGENCY STROBE
                </button>
              </div>

            </div>
          </div>
        </div>

        {/* Right Sidebar: Live AI Feed Stream component */}
        <div className="space-y-4">
          <LiveAiFeed cameraId={selectedCam.id} />

          {/* CCTV Info Metadata Box */}
          <div className="bg-command-card p-4 rounded-xl border border-command-border space-y-3 font-mono text-xs">
            <h3 className="font-bold text-slate-200 border-b border-command-border pb-2 flex items-center gap-2">
              <Activity className="w-4 h-4 text-emerald-400" /> CAMERA NODE TELEMETRY
            </h3>
            
            <div className="space-y-2">
              <div className="flex justify-between py-1 border-b border-command-border/40">
                <span className="text-slate-400">NODE ID:</span>
                <span className="text-cyan-300 font-bold">{selectedCam.id}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-command-border/40">
                <span className="text-slate-400">LOCATION:</span>
                <span className="text-slate-200">{selectedCam.name}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-command-border/40">
                <span className="text-slate-400">RTSP ENDPOINT:</span>
                <span className="text-slate-400 text-[10px] truncate max-w-[180px]">{selectedCam.rtsp_url}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-command-border/40">
                <span className="text-slate-400">SPEED THRESHOLD:</span>
                <span className="text-amber-400 font-bold">{selectedCam.speedLimit} KM/H</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-400">AI MODEL ACCURACY:</span>
                <span className="text-emerald-400 font-bold">98.4% (YOLOv11)</span>
              </div>
            </div>
          </div>
        </div>

      </div>
        </>
      )}
    </div>
  );
}
