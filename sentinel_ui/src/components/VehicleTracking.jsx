import React, { useState } from 'react';
import { Search, Car, AlertTriangle, ShieldCheck, MapPin, Clock, ShieldAlert, CheckCircle, FileText, ArrowRight } from 'lucide-react';

const MOCK_WATCHLIST_VEHICLES = [
  {
    plate: 'GJ-01-AB-1234',
    owner: 'Ramesh Patel',
    type: 'Sedan (White Hyundai Verna)',
    status: 'STOLEN VEHICLE ALERT',
    statusColor: 'bg-rose-500/20 text-rose-400 border-rose-500/40',
    lastSeenCamera: 'CAM-001 (SG Highway Iskcon)',
    lastSeenTime: '2 mins ago (09:06:12)',
    speed: '82 km/h',
    flaggedBy: 'Cyber Crime Cell & City Control Room',
    passages: [
      { cam: 'CAM-001 (SG Highway)', time: '09:06:12 IST', speed: '82 km/h', confidence: '98.8%' },
      { cam: 'CAM-002 (Riverfront East)', time: '08:52:40 IST', speed: '64 km/h', confidence: '97.2%' },
      { cam: 'CAM-004 (Expressway Toll)', time: '08:15:10 IST', speed: '95 km/h', confidence: '99.1%' },
    ]
  },
  {
    plate: 'GJ-05-CD-3321',
    owner: 'Apex Logistics Ltd',
    type: 'Heavy Truck (Tata Prima 3525)',
    status: 'OVER-SPEEDING VIOLATION',
    statusColor: 'bg-amber-500/20 text-amber-400 border-amber-500/40',
    lastSeenCamera: 'CAM-004 (Ahmedabad-Vadodara Toll)',
    lastSeenTime: '12 mins ago (08:56:01)',
    speed: '104 km/h (Limit: 80)',
    flaggedBy: 'Traffic Enforcement Radar',
    passages: [
      { cam: 'CAM-004 (Expressway Toll)', time: '08:56:01 IST', speed: '104 km/h', confidence: '99.4%' },
      { cam: 'CAM-003 (Surat Ring Road)', time: '07:30:15 IST', speed: '78 km/h', confidence: '96.5%' },
    ]
  },
  {
    plate: 'GJ-06-ZZ-9900',
    owner: 'Unknown Enterprise',
    type: 'Black SUV (Toyota Fortuner)',
    status: 'EXPIRED PERMIT / NO INSURANCE',
    statusColor: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40',
    lastSeenCamera: 'CAM-003 (Surat Textile Circle)',
    lastSeenTime: '25 mins ago (08:43:22)',
    speed: '52 km/h',
    flaggedBy: 'RTO Automated Scanning',
    passages: [
      { cam: 'CAM-003 (Surat Textile Circle)', time: '08:43:22 IST', speed: '52 km/h', confidence: '95.9%' }
    ]
  }
];

export default function VehicleTracking() {
  const [searchPlate, setSearchPlate] = useState('GJ-01-AB-1234');
  const [selectedVehicle, setSelectedVehicle] = useState(MOCK_WATCHLIST_VEHICLES[0]);
  const [isAlertDispatched, setIsAlertDispatched] = useState(false);

  const handleSearch = (e) => {
    e.preventDefault();
    const query = searchPlate.trim().toUpperCase();
    const match = MOCK_WATCHLIST_VEHICLES.find(v => v.plate.includes(query)) || {
      plate: query || 'GJ-18-BC-9988',
      owner: 'Gujarat Motor Vehicles Registry',
      type: 'Motorcycle / Private Vehicle',
      status: 'NORMAL — NO ACTIVE THREAT',
      statusColor: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
      lastSeenCamera: 'CAM-006 (Gandhinagar Secretariat)',
      lastSeenTime: '5 mins ago',
      speed: '48 km/h',
      flaggedBy: 'Standard ANPR Pass',
      passages: [
        { cam: 'CAM-006 (Gandhinagar Gate)', time: '09:03:00 IST', speed: '48 km/h', confidence: '99.0%' }
      ]
    };
    setSelectedVehicle(match);
  };

  const dispatchInterception = () => {
    setIsAlertDispatched(true);
    setTimeout(() => setIsAlertDispatched(false), 4000);
  };

  return (
    <div className="p-4 space-y-4 max-w-[1920px] mx-auto">
      
      {/* Top Banner & Search */}
      <div className="bg-command-card p-4 rounded-xl border border-command-border flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="font-mono font-extrabold text-slate-100 text-base uppercase tracking-wider flex items-center gap-2">
            <Car className="w-5 h-5 text-cyan-400" /> ANPR VEHICLE LOOKUP & ROUTE RECONSTRUCTION
          </h2>
          <p className="text-xs text-slate-400 font-mono">
            Statewide ANPR database query engine • Real-time license plate OCR scanning
          </p>
        </div>

        {/* Plate Search Bar */}
        <form onSubmit={handleSearch} className="flex items-center gap-2 w-full sm:w-auto">
          <div className="relative flex-1 sm:w-80">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              value={searchPlate}
              onChange={(e) => setSearchPlate(e.target.value)}
              placeholder="ENTER PLATE NUMBER (e.g. GJ-01-AB-1234)"
              className="w-full pl-9 pr-4 py-2 bg-command-bg border border-command-border rounded-lg text-xs font-mono text-cyan-300 uppercase tracking-widest focus:outline-none focus:border-cyan-500 shadow-inner"
            />
          </div>
          <button
            type="submit"
            className="px-4 py-2 bg-cyan-500/20 border border-cyan-500/40 text-cyan-300 rounded-lg font-mono text-xs font-bold hover:bg-cyan-500/30 transition shadow-glow-cyan"
          >
            SEARCH ANPR
          </button>
        </form>
      </div>

      {/* Main Grid: Watchlist Quick Select vs Detailed Vehicle Dossier */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        
        {/* Left Column: Watchlist Hit List */}
        <div className="space-y-3">
          <div className="bg-command-card p-3 rounded-xl border border-command-border">
            <h3 className="font-mono font-bold text-xs text-slate-200 uppercase tracking-wider mb-2 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-rose-400" /> RECENT ANPR WATCHLIST HITS
            </h3>
            
            <div className="space-y-2">
              {MOCK_WATCHLIST_VEHICLES.map((v) => (
                <div
                  key={v.plate}
                  onClick={() => setSelectedVehicle(v)}
                  className={`p-3 rounded-lg border font-mono text-xs cursor-pointer transition ${
                    selectedVehicle.plate === v.plate
                      ? 'bg-command-panel border-cyan-500/80 shadow-glow-cyan'
                      : 'bg-command-bg border-command-border hover:border-slate-500'
                  }`}
                >
                  <div className="flex justify-between items-center mb-1">
                    <span className="font-extrabold text-cyan-300 tracking-wider text-sm">{v.plate}</span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${v.statusColor}`}>
                      {v.status}
                    </span>
                  </div>

                  <p className="text-slate-300 text-[11px] font-medium">{v.type}</p>
                  
                  <div className="flex justify-between items-center text-[10px] text-slate-400 mt-2 pt-2 border-t border-command-border/60">
                    <span className="flex items-center gap-1">
                      <MapPin className="w-3 h-3 text-cyan-400" /> {v.lastSeenCamera.split(' ')[0]}
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3 text-emerald-400" /> {v.lastSeenTime}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Columns: Selected Vehicle Deep Dossier & Passage Timeline */}
        <div className="lg:col-span-2 space-y-4">
          
          {/* Dossier Header Card */}
          <div className="bg-command-card p-5 rounded-xl border border-command-border space-y-4">
            
            <div className="flex flex-wrap justify-between items-start gap-4 border-b border-command-border pb-4">
              <div>
                <span className="text-[10px] font-mono text-slate-400 uppercase tracking-widest">VEHICLE ANPR REGISTRATION DOSSIER</span>
                <h2 className="text-2xl font-mono font-extrabold text-cyan-300 tracking-widest mt-0.5">
                  {selectedVehicle.plate}
                </h2>
                <p className="text-slate-300 text-xs font-mono mt-1">{selectedVehicle.type}</p>
              </div>

              <div className="text-right font-mono">
                <span className={`inline-block px-3 py-1.5 rounded-lg text-xs font-extrabold border ${selectedVehicle.statusColor}`}>
                  {selectedVehicle.status}
                </span>
                <p className="text-[11px] text-slate-400 mt-1">FLAGGED BY: {selectedVehicle.flaggedBy}</p>
              </div>
            </div>

            {/* Vehicle Specs Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono text-xs">
              <div className="bg-command-bg p-3 rounded-lg border border-command-border">
                <span className="text-[10px] text-slate-400 block">REGISTERED OWNER</span>
                <span className="text-slate-100 font-semibold">{selectedVehicle.owner}</span>
              </div>

              <div className="bg-command-bg p-3 rounded-lg border border-command-border">
                <span className="text-[10px] text-slate-400 block">LAST DETECTED SPEED</span>
                <span className="text-amber-400 font-bold">{selectedVehicle.speed}</span>
              </div>

              <div className="bg-command-bg p-3 rounded-lg border border-command-border">
                <span className="text-[10px] text-slate-400 block">LAST CCTV NODE</span>
                <span className="text-cyan-300 font-semibold">{selectedVehicle.lastSeenCamera}</span>
              </div>

              <div className="bg-command-bg p-3 rounded-lg border border-command-border">
                <span className="text-[10px] text-slate-400 block">DETECTION CONFIDENCE</span>
                <span className="text-emerald-400 font-bold">98.8% (YOLO ANPR)</span>
              </div>
            </div>

            {/* Action Bar */}
            <div className="pt-2 flex items-center justify-between">
              {isAlertDispatched ? (
                <div className="bg-emerald-950 border border-emerald-500 text-emerald-300 px-4 py-2 rounded-lg text-xs font-mono font-bold flex items-center gap-2 animate-bounce">
                  <CheckCircle className="w-4 h-4 text-emerald-400" />
                  INTERCEPTION UNIT DISPATCHED TO {selectedVehicle.lastSeenCamera.split(' ')[0]}!
                </div>
              ) : (
                <button
                  onClick={dispatchInterception}
                  className="px-5 py-2.5 bg-rose-600 hover:bg-rose-500 text-white font-mono text-xs font-extrabold rounded-lg shadow-glow-alert flex items-center gap-2 transition"
                >
                  <ShieldAlert className="w-4 h-4" />
                  DISPATCH NEAREST PCR PATROL VAN TO INTERCEPT
                </button>
              )}

              <span className="text-[11px] font-mono text-slate-400">STATE POLICE NETWORK ENCRYPTED</span>
            </div>

          </div>

          {/* Passage Timeline Across Gujarat CCTV Nodes */}
          <div className="bg-command-card p-5 rounded-xl border border-command-border space-y-4 font-mono">
            <h3 className="font-bold text-xs text-slate-200 uppercase tracking-wider flex items-center gap-2">
              <MapPin className="w-4 h-4 text-cyan-400" /> CHRONOLOGICAL MOVEMENT PASSAGE TIMELINE
            </h3>

            <div className="space-y-3 relative before:absolute before:inset-0 before:left-3 before:w-0.5 before:bg-command-border">
              {selectedVehicle.passages.map((p, idx) => (
                <div key={idx} className="relative pl-8 flex items-center justify-between bg-command-bg p-3 rounded-lg border border-command-border">
                  <div className="absolute left-2.5 top-4 w-2 h-2 rounded-full bg-cyan-400 shadow-glow-cyan" />
                  
                  <div>
                    <h4 className="font-bold text-xs text-cyan-300 flex items-center gap-1.5">
                      {p.cam}
                    </h4>
                    <p className="text-[11px] text-slate-400 mt-0.5">
                      Passage Timestamp: <span className="text-slate-200 font-semibold">{p.time}</span>
                    </p>
                  </div>

                  <div className="text-right text-xs">
                    <span className="text-amber-400 font-bold block">{p.speed}</span>
                    <span className="text-[10px] text-emerald-400">OCR Match: {p.confidence}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

        </div>

      </div>
    </div>
  );
}
