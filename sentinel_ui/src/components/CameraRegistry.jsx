import React, { useState } from 'react';
import { Database, Search, Plus, Filter, CheckCircle2, XCircle, Camera, RefreshCw } from 'lucide-react';

const MOCK_CAMERAS = [
  { id: 'CAM-001', name: 'SG Highway Iskcon Crossroad', district: 'Ahmedabad', ip: '10.42.0.101', proto: 'RTSP / ONVIF', res: '1920x1080 (60 FPS)', codec: 'H.265 / HEVC', status: 'ONLINE' },
  { id: 'CAM-002', name: 'Sabarmati Riverfront Promenade', district: 'Ahmedabad', ip: '10.42.0.102', proto: 'RTSP / ONVIF', res: '3840x2160 (30 FPS)', codec: 'H.265 / 4K', status: 'ONLINE' },
  { id: 'CAM-003', name: 'Surat Textile Market Circle', district: 'Surat', ip: '10.42.0.201', proto: 'RTSP / ONVIF', res: '1920x1080 (60 FPS)', codec: 'H.264', status: 'ONLINE' },
  { id: 'CAM-004', name: 'Ahmedabad-Vadodara Express Toll', district: 'Vadodara Toll', ip: '10.42.0.301', proto: 'RTSP / ONVIF', res: '3840x2160 (60 FPS)', codec: 'H.265 / 4K', status: 'ONLINE' },
  { id: 'CAM-005', name: 'Rajkot Trikon Baug Junction', district: 'Rajkot', ip: '10.42.0.401', proto: 'RTSP / ONVIF', res: '1920x1080 (30 FPS)', codec: 'H.264', status: 'ONLINE' },
  { id: 'CAM-006', name: 'Gandhinagar Swarnim Park VIP Gate', district: 'Gandhinagar', ip: '10.42.0.501', proto: 'RTSP / ONVIF', res: '3840x2160 (60 FPS)', codec: 'H.265 / 4K', status: 'ONLINE' },
  { id: 'CAM-007', name: 'Bhavnagar Port Access Corridor', district: 'Bhavnagar', ip: '10.42.0.601', proto: 'RTSP / ONVIF', res: '1920x1080 (30 FPS)', codec: 'H.264', status: 'ONLINE' },
  { id: 'CAM-008', name: 'Jamnagar Reliance Highway Gate', district: 'Jamnagar', ip: '10.42.0.701', proto: 'RTSP / ONVIF', res: '1920x1080 (60 FPS)', codec: 'H.265', status: 'ONLINE' },
];

export default function CameraRegistry() {
  const [searchTerm, setSearchTerm] = useState('');
  const [districtFilter, setDistrictFilter] = useState('ALL');

  const filtered = MOCK_CAMERAS.filter(c => {
    const matchSearch = c.name.toLowerCase().includes(searchTerm.toLowerCase()) || c.id.toLowerCase().includes(searchTerm.toLowerCase()) || c.ip.includes(searchTerm);
    const matchDistrict = districtFilter === 'ALL' || c.district.toLowerCase().includes(districtFilter.toLowerCase());
    return matchSearch && matchDistrict;
  });

  return (
    <div className="p-4 space-y-4 max-w-[1920px] mx-auto font-mono text-xs">
      
      {/* Top Banner */}
      <div className="bg-command-card p-4 rounded-xl border border-command-border flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="font-extrabold text-slate-100 text-base uppercase tracking-wider flex items-center gap-2">
            <Database className="w-5 h-5 text-cyan-400" /> STATEWIDE CCTV CAMERA INVENTORY & REGISTRY
          </h2>
          <p className="text-xs text-slate-400">
            Hardware catalogue, RTSP endpoints, IP management & video codec configurations (1,420 registered nodes)
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="SEARCH CAMERA ID, NAME OR IP..."
              className="pl-9 pr-3 py-2 bg-command-bg border border-command-border rounded-lg text-slate-200 focus:outline-none focus:border-cyan-500 w-64"
            />
          </div>

          <select
            value={districtFilter}
            onChange={(e) => setDistrictFilter(e.target.value)}
            className="px-3 py-2 bg-command-bg border border-command-border rounded-lg text-slate-200 focus:outline-none focus:border-cyan-500"
          >
            <option value="ALL">ALL DISTRICTS</option>
            <option value="Ahmedabad">AHMEDABAD</option>
            <option value="Surat">SURAT</option>
            <option value="Vadodara">VADODARA</option>
            <option value="Rajkot">RAJKOT</option>
            <option value="Gandhinagar">GANDHINAGAR</option>
          </select>
        </div>
      </div>

      {/* Camera Catalogue Table */}
      <div className="bg-command-card p-4 rounded-xl border border-command-border space-y-3">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-command-border text-slate-400 text-[11px]">
                <th className="py-2.5 px-3">NODE ID</th>
                <th className="py-2.5 px-3">CAMERA NAME & LOCATION</th>
                <th className="py-2.5 px-3">DISTRICT</th>
                <th className="py-2.5 px-3">IP ADDRESS</th>
                <th className="py-2.5 px-3">STREAM PROTOCOL</th>
                <th className="py-2.5 px-3">RESOLUTION & FPS</th>
                <th className="py-2.5 px-3">CODEC</th>
                <th className="py-2.5 px-3 text-right">STATUS</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-command-border/40">
              {filtered.map((cam) => (
                <tr key={cam.id} className="hover:bg-command-bg/50 transition">
                  <td className="py-3 px-3 text-cyan-300 font-extrabold">{cam.id}</td>
                  <td className="py-3 px-3 text-slate-100 font-semibold">{cam.name}</td>
                  <td className="py-3 px-3 text-slate-300">{cam.district}</td>
                  <td className="py-3 px-3 text-slate-400 font-mono text-[11px]">{cam.ip}</td>
                  <td className="py-3 px-3 text-cyan-400">{cam.proto}</td>
                  <td className="py-3 px-3 text-slate-200">{cam.res}</td>
                  <td className="py-3 px-3 text-slate-400">{cam.codec}</td>
                  <td className="py-3 px-3 text-right">
                    <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 text-[10px] font-bold">
                      ● {cam.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
}
