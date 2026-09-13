import React, { useEffect, useState } from 'react';
import { getAiDetections, subscribeAiEvents } from '../../services/liveAiService';

export default function LiveAiFeed({ cameraId }) {
  const [events, setEvents] = useState([]);
  const [error, setError] = useState('');
  const [filterMode, setFilterMode] = useState('ALL'); // 'ALL' | 'VEHICLES' | 'FACES'

  useEffect(() => {
    let mounted = true;
    getAiDetections({ cameraId, limit: 30 })
      .then(x => {
        if (mounted) setEvents(x);
      })
      .catch(e => mounted && setError(e.message));

    const unsubscribe = subscribeAiEvents(e => {
      if (!cameraId || e.camera_id === cameraId) {
        setEvents(prev => [e, ...prev].slice(0, 50));
      }
    });
    return () => {
      mounted = false;
      unsubscribe();
    };
  }, [cameraId]);

  const filteredEvents = events.filter(e => {
    if (filterMode === 'VEHICLES') {
      return e.detection_type?.includes('Vehicle') || e.detection_type?.includes('OCR') || e.detection_type?.includes('ANPR');
    }
    if (filterMode === 'FACES') {
      return e.detection_type?.includes('InsightFace') || e.detection_type?.includes('Watchlist') || e.detection_type?.includes('Citizen');
    }
    return true;
  });

  return (
    <div className="bg-command-card border border-command-border rounded-lg p-4 font-mono">
      <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
        <h3 className="font-mono font-bold text-xs text-slate-200">LIVE AI DETECTIONS</h3>
        <span className="text-emerald-400 text-[11px] font-bold">● STREAMING</span>
      </div>

      {/* Filter Category Selector */}
      <div className="flex bg-command-bg p-1 rounded-md border border-command-border gap-1 text-[10px] mb-3">
        <button
          onClick={() => setFilterMode('ALL')}
          className={`flex-1 py-1 rounded font-bold transition ${
            filterMode === 'ALL' ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40' : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          🌐 ALL ({events.length})
        </button>
        <button
          onClick={() => setFilterMode('VEHICLES')}
          className={`flex-1 py-1 rounded font-bold transition ${
            filterMode === 'VEHICLES' ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40' : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          🚗 VEHICLES
        </button>
        <button
          onClick={() => setFilterMode('FACES')}
          className={`flex-1 py-1 rounded font-bold transition ${
            filterMode === 'FACES' ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40' : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          👤 FACES
        </button>
      </div>

      {error && <div className="text-rose-400 text-xs mb-2">{error}</div>}

      <div className="space-y-2 max-h-72 overflow-auto">
        {filteredEvents.map((e, i) => {
          const isWanted = e.label?.includes('WANTED');
          const isCitizen = e.label?.includes('CITIZEN');

          return (
            <div
              key={e.id || i}
              className={`p-2 rounded border text-xs space-y-1 transition ${
                isWanted
                  ? 'bg-rose-950/60 border-rose-600/60 text-rose-200 animate-pulse'
                  : isCitizen
                  ? 'bg-emerald-950/40 border-emerald-600/40 text-emerald-200'
                  : 'bg-command-surface border-command-border text-slate-300'
              }`}
            >
              <div className="flex justify-between items-center text-[10px]">
                <span className="font-bold text-cyan-300">{e.camera_id}</span>
                <span className="text-slate-400">{e.timestamp || 'LIVE'}</span>
              </div>
              <div className="font-bold text-[11px] truncate">{e.label}</div>
              <div className="flex justify-between text-[10px] text-slate-400">
                <span>{e.detection_type}</span>
                <span className="font-bold text-emerald-400">
                  {e.confidence ? `${(e.confidence * 100).toFixed(1)}%` : '—'}
                </span>
              </div>
            </div>
          );
        })}
        {!filteredEvents.length && (
          <div className="text-slate-500 text-xs text-center py-4">No AI detection events match filter.</div>
        )}
      </div>
    </div>
  );
}
