import React, { useState } from 'react';
import { ShieldCheck, ShieldAlert, Plus, Search, Car, User, AlertTriangle, CheckCircle, Trash2 } from 'lucide-react';

const INITIAL_WATCHLIST = [
  {
    plate: 'GJ-01-AB-1234',
    category: 'STOLEN VEHICLE',
    owner: 'Ramesh Patel',
    vehicleDesc: 'White Hyundai Verna 2022',
    flaggedDate: '08 Sep 2026',
    threatLevel: 'CRITICAL',
    matchedHits: 14,
    lastCamera: 'CAM-001 (SG Highway)'
  },
  {
    plate: 'GJ-05-CD-3321',
    category: 'HABITUAL OVERSPEEDER',
    owner: 'Apex Logistics Ltd',
    vehicleDesc: 'Tata Prima Heavy Truck (3525)',
    flaggedDate: '01 Sep 2026',
    threatLevel: 'HIGH',
    matchedHits: 8,
    lastCamera: 'CAM-004 (Vadodara Toll)'
  },
  {
    plate: 'GJ-06-ZZ-9900',
    category: 'SUSPECTED DRUG TRAFFICKING',
    owner: 'Unknown (Fake RC Entry)',
    vehicleDesc: 'Black Toyota Fortuner',
    flaggedDate: '28 Aug 2026',
    threatLevel: 'CRITICAL',
    matchedHits: 5,
    lastCamera: 'CAM-003 (Surat Ring Road)'
  },
  {
    plate: 'GJ-18-Z-4411',
    category: 'EXPIRED STATE PERMIT',
    owner: 'Commercial Transport Fleet',
    vehicleDesc: 'Ashok Leyland Bus',
    flaggedDate: '15 Aug 2026',
    threatLevel: 'MEDIUM',
    matchedHits: 2,
    lastCamera: 'CAM-006 (Gandhinagar Gate)'
  }
];

export default function WatchlistRegistry() {
  const [watchlist, setWatchlist] = useState(INITIAL_WATCHLIST);
  const [searchQuery, setSearchQuery] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [newPlate, setNewPlate] = useState('');
  const [newCategory, setNewCategory] = useState('STOLEN VEHICLE');
  const [newDesc, setNewDesc] = useState('');

  const handleAdd = (e) => {
    e.preventDefault();
    if (!newPlate.trim()) return;
    const newItem = {
      plate: newPlate.trim().toUpperCase(),
      category: newCategory,
      owner: 'Gujarat Police Intelligence Unit',
      vehicleDesc: newDesc || 'Target Vehicle for Tracking',
      flaggedDate: 'Just Now',
      threatLevel: newCategory.includes('STOLEN') ? 'CRITICAL' : 'HIGH',
      matchedHits: 0,
      lastCamera: 'Statewide Radar Scan'
    };
    setWatchlist([newItem, ...watchlist]);
    setNewPlate('');
    setNewDesc('');
    setShowAddModal(false);
  };

  const handleDelete = (plate) => {
    setWatchlist(watchlist.filter(w => w.plate !== plate));
  };

  const filtered = watchlist.filter(w => 
    w.plate.includes(searchQuery.toUpperCase()) || 
    w.category.toLowerCase().includes(searchQuery.toLowerCase()) ||
    w.vehicleDesc.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="p-4 space-y-4 max-w-[1920px] mx-auto font-mono text-xs">
      
      {/* Top Banner & Actions */}
      <div className="bg-command-card p-4 rounded-xl border border-command-border flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="font-extrabold text-slate-100 text-base uppercase tracking-wider flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-cyan-400" /> STATE POLICE WATCHLIST & HOT LIST REGISTRY
          </h2>
          <p className="text-xs text-slate-400">
            Automated ANPR match trigger database for stolen, suspect, and high-risk flagged vehicles
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="SEARCH WATCHLIST PLATES..."
              className="pl-9 pr-3 py-2 bg-command-bg border border-command-border rounded-lg text-slate-200 focus:outline-none focus:border-cyan-500 uppercase"
            />
          </div>

          <button
            onClick={() => setShowAddModal(true)}
            className="px-4 py-2 bg-cyan-500/20 hover:bg-cyan-500/30 border border-cyan-500/40 text-cyan-300 rounded-lg font-bold flex items-center gap-1.5 transition shadow-glow-cyan"
          >
            <Plus className="w-4 h-4" /> ADD VEHICLE TO WATCHLIST
          </button>
        </div>
      </div>

      {/* Watchlist Table */}
      <div className="bg-command-card p-4 rounded-xl border border-command-border space-y-3">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-command-border text-slate-400 text-[11px]">
                <th className="py-2.5 px-3">LICENSE PLATE</th>
                <th className="py-2.5 px-3">ALERT REASON</th>
                <th className="py-2.5 px-3">VEHICLE DETAILS</th>
                <th className="py-2.5 px-3">REGISTERED OWNER</th>
                <th className="py-2.5 px-3">DATE FLAGGED</th>
                <th className="py-2.5 px-3">ANPR HITS</th>
                <th className="py-2.5 px-3">THREAT LEVEL</th>
                <th className="py-2.5 px-3 text-right">ACTION</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-command-border/40">
              {filtered.map((item) => (
                <tr key={item.plate} className="hover:bg-command-bg/50 transition">
                  <td className="py-3 px-3">
                    <span className="text-cyan-300 font-extrabold text-sm tracking-wider">{item.plate}</span>
                  </td>
                  <td className="py-3 px-3">
                    <span className="text-slate-200 font-semibold">{item.category}</span>
                  </td>
                  <td className="py-3 px-3 text-slate-300">{item.vehicleDesc}</td>
                  <td className="py-3 px-3 text-slate-400">{item.owner}</td>
                  <td className="py-3 px-3 text-slate-400">{item.flaggedDate}</td>
                  <td className="py-3 px-3">
                    <span className="text-amber-400 font-bold">{item.matchedHits} passage hits</span>
                  </td>
                  <td className="py-3 px-3">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      item.threatLevel === 'CRITICAL' ? 'bg-rose-500/20 text-rose-400 border border-rose-500/40' :
                      'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                    }`}>
                      {item.threatLevel}
                    </span>
                  </td>
                  <td className="py-3 px-3 text-right">
                    <button
                      onClick={() => handleDelete(item.plate)}
                      className="p-1.5 rounded hover:bg-rose-500/20 text-slate-400 hover:text-rose-400 transition"
                      title="Remove from Watchlist"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-command-card border border-cyan-500/60 p-6 rounded-2xl max-w-md w-full shadow-2xl space-y-4">
            <h3 className="font-extrabold text-slate-100 text-sm flex items-center gap-2 border-b border-command-border pb-3">
              <ShieldAlert className="w-5 h-5 text-cyan-400" /> REGISTER VEHICLE TO STATE WATCHLIST
            </h3>

            <form onSubmit={handleAdd} className="space-y-3">
              <div>
                <label className="text-[11px] text-slate-400 block mb-1">LICENSE PLATE NUMBER *</label>
                <input
                  type="text"
                  required
                  value={newPlate}
                  onChange={(e) => setNewPlate(e.target.value)}
                  placeholder="e.g. GJ-01-XY-9999"
                  className="w-full px-3 py-2 bg-command-bg border border-command-border rounded-lg text-cyan-300 uppercase font-bold focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="text-[11px] text-slate-400 block mb-1">WATCHLIST CATEGORY</label>
                <select
                  value={newCategory}
                  onChange={(e) => setNewCategory(e.target.value)}
                  className="w-full px-3 py-2 bg-command-bg border border-command-border rounded-lg text-slate-200 focus:outline-none focus:border-cyan-500"
                >
                  <option value="STOLEN VEHICLE">STOLEN VEHICLE</option>
                  <option value="HABITUAL OVERSPEEDER">HABITUAL OVERSPEEDER</option>
                  <option value="SUSPECTED CRIME LINK">SUSPECTED CRIME LINK</option>
                  <option value="UNPAID E-CHALLANS">UNPAID E-CHALLANS (OVERDUE)</option>
                  <option value="VIP SECURITY CORRIDOR">VIP SECURITY CORRIDOR</option>
                </select>
              </div>

              <div>
                <label className="text-[11px] text-slate-400 block mb-1">VEHICLE DESCRIPTION</label>
                <input
                  type="text"
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  placeholder="e.g. Red Maruti Swift 2023"
                  className="w-full px-3 py-2 bg-command-bg border border-command-border rounded-lg text-slate-200 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-command-border">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 bg-command-bg border border-command-border text-slate-300 rounded-lg"
                >
                  CANCEL
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-cyan-500/20 border border-cyan-500/50 text-cyan-300 font-bold rounded-lg shadow-glow-cyan"
                >
                  SAVE TO WATCHLIST
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
}
