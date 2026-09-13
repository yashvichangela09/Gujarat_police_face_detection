import React, { useState, useEffect, useRef } from 'react';
import { 
  Map as MapIcon, MapPin, Radio, Camera, ShieldAlert, Eye, Activity, 
  ZoomIn, ZoomOut, RotateCcw, Layers, Search, Navigation, 
  Info, ExternalLink, SlidersHorizontal, CheckCircle2
} from 'lucide-react';
import L from 'leaflet';

const GIS_NODES = [
  {
    id: 'CAM-001',
    camNum: '1',
    name: 'SG Highway Iskcon Crossroad CCTV',
    city: 'Ahmedabad',
    district: 'Ahmedabad District',
    lat: 23.0275,
    lng: 72.5066,
    status: 'ONLINE',
    threat: 'ALERT_ACTIVE',
    res: '1920 x 1080 (1080p FHD)',
    codec: 'H.265 / HEVC',
    fps: '59.94 FPS',
    speedAvg: '68 km/h',
    vehicles: 142
  },
  {
    id: 'CAM-002',
    camNum: '2',
    name: 'Sabarmati Riverfront Promenade CCTV',
    city: 'Ahmedabad',
    district: 'Ahmedabad District',
    lat: 23.0300,
    lng: 72.5800,
    status: 'ONLINE',
    threat: 'NORMAL',
    res: '3840 x 2160 (4K UHD)',
    codec: 'H.265 / HEVC',
    fps: '29.97 FPS',
    speedAvg: '42 km/h',
    vehicles: 88
  },
  {
    id: 'CAM-003',
    camNum: '3',
    name: 'Surat Textile Market Ring Road CCTV',
    city: 'Surat',
    district: 'Surat District',
    lat: 21.1702,
    lng: 72.8311,
    status: 'ONLINE',
    threat: 'HEAVY_TRAFFIC',
    res: '1920 x 1080 (1080p FHD)',
    codec: 'H.264',
    fps: '59.94 FPS',
    speedAvg: '28 km/h',
    vehicles: 310
  },
  {
    id: 'CAM-004',
    camNum: '4',
    name: 'Ahmedabad-Vadodara Express Tollway CCTV',
    city: 'Vadodara Toll',
    district: 'Vadodara District',
    lat: 22.3072,
    lng: 73.1812,
    status: 'ONLINE',
    threat: 'ALERT_ACTIVE',
    res: '3840 x 2160 (4K UHD)',
    codec: 'H.265 / HEVC',
    fps: '59.94 FPS',
    speedAvg: '94 km/h',
    vehicles: 205
  },
  {
    id: 'CAM-017',
    camNum: '17',
    name: '17 Rajkot Bus Port Junction CCTV',
    city: 'Rajkot',
    district: 'Rajkot District',
    lat: 22.3039,
    lng: 70.8022,
    status: 'ONLINE',
    threat: 'NORMAL',
    res: '1920 x 1080 (1080p FHD)',
    codec: 'H.265 / HEVC',
    fps: '24.98 FPS',
    speedAvg: '45 km/h',
    vehicles: 95
  },
  {
    id: 'CAM-006',
    camNum: '6',
    name: 'Gandhinagar Swarnim Park VIP Gate CCTV',
    city: 'Gandhinagar',
    district: 'Gandhinagar District',
    lat: 23.2156,
    lng: 72.6369,
    status: 'ONLINE',
    threat: 'NORMAL',
    res: '3840 x 2160 (4K UHD)',
    codec: 'H.265 / HEVC',
    fps: '59.94 FPS',
    speedAvg: '50 km/h',
    vehicles: 64
  },
  {
    id: 'CAM-015',
    camNum: '15',
    name: 'Bhavnagar Port Access Corridor CCTV',
    city: 'Bhavnagar',
    district: 'Bhavnagar District',
    lat: 21.7645,
    lng: 72.1519,
    status: 'ONLINE',
    threat: 'NORMAL',
    res: '1920 x 1080 (1080p FHD)',
    codec: 'H.264',
    fps: '29.97 FPS',
    speedAvg: '55 km/h',
    vehicles: 72
  },
  {
    id: 'CAM-019',
    camNum: '19',
    name: 'Jamnagar Reliance Highway Gate CCTV',
    city: 'Jamnagar',
    district: 'Jamnagar District',
    lat: 22.4707,
    lng: 70.0577,
    status: 'ONLINE',
    threat: 'NORMAL',
    res: '1920 x 1080 (1080p FHD)',
    codec: 'H.265 / HEVC',
    fps: '59.94 FPS',
    speedAvg: '62 km/h',
    vehicles: 110
  }
];

export default function GisMap({ onSelectCamera }) {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const markersRef = useRef([]);
  const [selectedNode, setSelectedNode] = useState(GIS_NODES.find(n => n.id === 'CAM-017') || GIS_NODES[0]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedDistrict, setSelectedDistrict] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [mapLayer, setMapLayer] = useState('dark');

  useEffect(() => {
    if (!mapContainerRef.current) return;

    // Strict cleanup for React 18
    if (mapContainerRef.current._leaflet_id) {
      delete mapContainerRef.current._leaflet_id;
    }
    if (mapInstanceRef.current) {
      try {
        mapInstanceRef.current.remove();
      } catch (e) {}
      mapInstanceRef.current = null;
    }

    try {
      const map = new L.Map(mapContainerRef.current, {
        center: [22.4, 71.9],
        zoom: 7.5,
        zoomControl: false,
        attributionControl: false
      });
      mapInstanceRef.current = map;

      const tileUrl = mapLayer === 'satellite'
        ? 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
        : 'https://services.arcgisonline.com/arcgis/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}';

      L.tileLayer(tileUrl, { maxZoom: 18 }).addTo(map);

      if (mapLayer === 'dark') {
        L.tileLayer('https://services.arcgisonline.com/arcgis/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}', { maxZoom: 18 }).addTo(map);
      }

      markersRef.current = [];
      GIS_NODES.forEach((node) => {
        const isAlert = node.threat === 'ALERT_ACTIVE';
        const isHeavy = node.threat === 'HEAVY_TRAFFIC';
        const color = isAlert ? '#ff2a6d' : isHeavy ? '#ffb703' : '#00f5d4';

        const customIcon = L.divIcon({
          className: 'custom-leaflet-marker',
          html: `
            <div style="display: flex; flex-direction: column; align-items: center; cursor: pointer;">
              <div style="background: rgba(12, 18, 32, 0.9); border: 1px solid ${color}; color: #e2e8f0; font-size: 9px; font-weight: bold; padding: 1px 4px; border-radius: 3px; font-family: monospace; white-space: nowrap; margin-bottom: 2px;">
                ${node.id}
              </div>
              <div style="position: relative; width: 26px; height: 26px; display: flex; align-items: center; justify-content: center;">
                <div style="position: absolute; inset: -3px; border-radius: 50%; background-color: ${color}; opacity: 0.45; animation: ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite;"></div>
                <div style="position: relative; width: 22px; height: 22px; border-radius: 50%; background: #060810; border: 2px solid ${color}; color: ${color}; display: flex; align-items: center; justify-content: center; font-size: 10px;">
                  📷
                </div>
              </div>
            </div>
          `,
          iconSize: [40, 44],
          iconAnchor: [20, 36]
        });

        const marker = L.marker([node.lat, node.lng], { icon: customIcon }).addTo(map);
        marker.on('click', () => setSelectedNode(node));
        markersRef.current.push({ id: node.id, marker });
      });
    } catch (err) {
      console.warn('Leaflet initialization warning:', err);
    }

    return () => {
      if (mapInstanceRef.current) {
        try {
          mapInstanceRef.current.remove();
        } catch (e) {}
        mapInstanceRef.current = null;
      }
      if (mapContainerRef.current) {
        delete mapContainerRef.current._leaflet_id;
      }
    };
  }, [mapLayer]);

  const zoomIn = () => mapInstanceRef.current && mapInstanceRef.current.zoomIn();
  const zoomOut = () => mapInstanceRef.current && mapInstanceRef.current.zoomOut();
  const locateGujarat = () => {
    if (mapInstanceRef.current) {
      mapInstanceRef.current.setView([selectedNode.lat, selectedNode.lng], 12, { animate: true });
    }
  };

  return (
    <div className="p-4 space-y-3 max-w-[1920px] mx-auto font-mono text-xs">
      
      {/* Top Banner Exactly Matching User Reference */}
      <div className="bg-command-card p-4 rounded-xl border border-command-border flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
            <MapIcon className="w-5 h-5 text-cyan-400" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="font-extrabold text-slate-100 text-sm tracking-wider uppercase">
                GIS SURVEILLANCE RADAR
              </h2>
              <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-500/40 text-[10px] font-bold">
                ● CARTOGRAPHIC ENGINE ACTIVE
              </span>
            </div>
            <p className="text-[11px] text-slate-400 mt-0.5">
              Geospatial telemetry and surveillance sector mapping across Gujarat State
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 text-slate-400 text-[11px] bg-command-bg px-3 py-1.5 rounded-lg border border-command-border">
          <Info className="w-3.5 h-3.5 text-cyan-400" />
          <span>REAL CATALOGUE METADATA + ESTIMATED GUJARAT GIS COORDS</span>
        </div>
      </div>

      {/* Main Map Box with Floating Controls and Bottom Active Camera Card */}
      <div className="bg-command-card rounded-xl border border-command-border relative overflow-hidden h-[620px] flex flex-col justify-between">
        
        {/* Top Floating Controls inside Map */}
        <div className="absolute top-4 left-4 right-4 z-[1000] flex flex-wrap items-center justify-between gap-3 pointer-events-none">
          
          {/* Search Map Nodes & District Dropdown */}
          <div className="flex items-center gap-2 pointer-events-auto bg-[#080d1a]/95 backdrop-blur p-1.5 rounded-xl border border-command-border shadow-xl">
            <div className="relative">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search map nodes..."
                className="pl-9 pr-3 py-1.5 bg-command-bg border border-command-border rounded-lg text-slate-200 text-xs focus:outline-none focus:border-cyan-500 w-48 sm:w-60"
              />
            </div>

            <select
              value={selectedDistrict}
              onChange={(e) => setSelectedDistrict(e.target.value)}
              className="px-3 py-1.5 bg-command-bg border border-command-border rounded-lg text-slate-200 text-xs focus:outline-none focus:border-cyan-500"
            >
              <option value="ALL">All Districts</option>
              <option value="Ahmedabad">Ahmedabad</option>
              <option value="Surat">Surat</option>
              <option value="Vadodara">Vadodara</option>
              <option value="Rajkot">Rajkot</option>
              <option value="Gandhinagar">Gandhinagar</option>
            </select>
          </div>

          {/* Right Status Filter Pills */}
          <div className="flex items-center gap-1.5 pointer-events-auto bg-[#080d1a]/95 backdrop-blur p-1.5 rounded-xl border border-command-border shadow-xl font-mono text-xs">
            {['ALL', 'ONLINE', 'OFFLINE'].map((st) => (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                className={`px-3 py-1.5 rounded-lg font-bold transition ${
                  statusFilter === st
                    ? 'bg-blue-600 text-white shadow-lg'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {st}
              </button>
            ))}

            <button
              onClick={locateGujarat}
              className="p-2 rounded-lg bg-command-bg border border-command-border hover:border-cyan-500 text-cyan-400 transition"
              title="Locate selected node"
            >
              <Navigation className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Leaflet Target Container */}
        <div ref={mapContainerRef} className="w-full h-full z-10" />

        {/* Floating Zoom & Layer Buttons on the Right */}
        <div className="absolute right-4 bottom-28 z-[1000] flex flex-col gap-1.5 font-mono">
          <button
            onClick={zoomIn}
            className="w-8 h-8 rounded-lg bg-[#080d1a]/95 hover:bg-cyan-500/20 text-cyan-300 border border-command-border flex items-center justify-center font-bold text-base shadow-xl"
          >
            +
          </button>
          <button
            onClick={zoomOut}
            className="w-8 h-8 rounded-lg bg-[#080d1a]/95 hover:bg-cyan-500/20 text-cyan-300 border border-command-border flex items-center justify-center font-bold text-base shadow-xl"
          >
            -
          </button>
          <button
            onClick={() => setMapLayer(mapLayer === 'dark' ? 'satellite' : 'dark')}
            className="p-2 rounded-lg bg-[#080d1a]/95 hover:bg-cyan-500/20 text-cyan-300 border border-command-border flex items-center justify-center shadow-xl"
            title="Toggle Satellite Imagery"
          >
            <Layers className="w-4 h-4" />
          </button>
        </div>

        {/* Bottom Selected Node Overlay Bar */}
        <div className="absolute bottom-4 left-4 right-4 z-[1000] bg-[#0c1222]/95 backdrop-blur-md p-4 rounded-xl border border-cyan-500/40 shadow-2xl flex flex-wrap items-center justify-between gap-4 font-mono">
          
          {/* Left Node Details */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-950/80 border border-cyan-500/40 flex items-center justify-center text-cyan-400 shrink-0">
              <Camera className="w-5 h-5" />
            </div>

            <div>
              <div className="flex items-center gap-3 flex-wrap">
                <span className="font-extrabold text-cyan-300 text-sm">{selectedNode.id}</span>
                <span className="text-slate-400">| Camera {selectedNode.camNum}</span>
                <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-500/40 text-[10px] font-bold">
                  ● {selectedNode.status}
                </span>
                <span className="text-slate-300 text-xs">{selectedNode.res}</span>
                <span className="text-slate-400 text-xs">• {selectedNode.codec}</span>
                <span className="text-cyan-400 text-xs">• {selectedNode.fps}</span>
              </div>
              <p className="text-slate-300 text-xs mt-0.5">
                {selectedNode.name} ({selectedNode.district})
              </p>
            </div>
          </div>

          {/* Right Action Buttons */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => alert(`Camera Telemetry:\nNode: ${selectedNode.id}\nGPS: ${selectedNode.lat}, ${selectedNode.lng}\nVehicles: ${selectedNode.vehicles}\nAvg Speed: ${selectedNode.speedAvg}`)}
              className="px-3.5 py-2 rounded-lg bg-command-bg border border-command-border hover:border-slate-400 text-slate-200 font-bold text-xs flex items-center gap-1.5 transition"
            >
              <Eye className="w-3.5 h-3.5 text-cyan-400" /> Details
            </button>

            <button
              onClick={() => onSelectCamera && onSelectCamera(selectedNode)}
              className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs flex items-center gap-1.5 transition shadow-lg"
            >
              <Camera className="w-3.5 h-3.5" /> View Live Feed
            </button>
          </div>

        </div>

      </div>

    </div>
  );
}
