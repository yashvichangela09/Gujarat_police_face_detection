import React, {useEffect, useState} from 'react';
import {getAiDetections, subscribeAiEvents} from '../../services/liveAiService';

export default function LiveAiFeed({cameraId}) {
  const [events,setEvents]=useState([]);
  const [error,setError]=useState('');

  useEffect(()=>{
    let mounted=true;
    getAiDetections({cameraId,limit:30}).then(x=>{
      if(mounted)setEvents(x);
    }).catch(e=>mounted&&setError(e.message));
    const unsubscribe=subscribeAiEvents(e=>{
      if(!cameraId || e.camera_id===cameraId) {
        setEvents(prev=>[e,...prev].slice(0,50));
      }
    });
    return ()=>{mounted=false;unsubscribe();};
  },[cameraId]);

  return <div className="bg-command-card border border-command-border rounded-lg p-4">
    <div className="flex justify-between mb-3">
      <h3 className="font-mono font-bold">LIVE AI DETECTIONS</h3>
      <span className="text-emerald-400 text-xs">● STREAMING</span>
    </div>
    {error && <div className="text-rose-400 text-xs mb-2">{error}</div>}
    <div className="space-y-2 max-h-72 overflow-auto">
      {events.map((e,i)=><div key={e.id||i}
        className="flex items-center justify-between p-2 rounded bg-command-surface border border-command-border text-xs">
        <span>{e.camera_id}</span>
        <span className="text-cyan-300">{e.detection_type}</span>
        <span>{e.label}</span>
        <span>{e.confidence ? `${(e.confidence*100).toFixed(1)}%` : '—'}</span>
        <span>{e.track_id ?? '—'}</span>
      </div>)}
      {!events.length && <div className="text-command-muted text-xs">No AI events yet.</div>}
    </div>
  </div>;
}
