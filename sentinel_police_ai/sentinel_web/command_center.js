/**
 * command_center.js
 * SENTINEL AI Command Center Client
 * Handles real-time multi-camera telemetry, high-speed auto-sync polling,
 * cross-camera transition feed, live vehicle event log, and the
 * Central Vehicle Identity Dossier Matrix (Identity Cards).
 */

// Safe optional Socket.IO initialization
let socket = null;
if (typeof io !== 'undefined') {
  try {
    socket = io();
  } catch (e) {
    console.warn('[SENTINEL] Socket.IO initialization skipped:', e);
  }
}

// State caches & deduplication
let allDetections = [];
let crossEventsCount = 0;
let knownVehicles = new Set();
let knownPlates = new Set();
let totalDetectionsCount = 0;
let totalPlatesCount = 0;
const seenDetectionKeys = new Set();
const seenTransitionIds = new Set();

// Identity Dossier State
let allRegisteredVehicles = [];
let activeIdFilter = 'all';
let idSearchQuery = '';

// Element helper
const $ = (id) => document.getElementById(id);

// Color helper for paint dot
function getColorHex(colorName) {
  const map = {
    'white': '#ffffff',
    'black': '#1f2937',
    'silver': '#94a3b8',
    'grey': '#64748b',
    'gray': '#64748b',
    'red': '#ef4444',
    'blue': '#3b82f6',
    'yellow': '#eab308',
    'green': '#22c55e',
    'brown': '#78350f',
  };
  return map[(colorName || '').toLowerCase()] || '#64748b';
}

// ── Clock & Date ──────────────────────────────────────────────────────────
function initClock() {
  function update() {
    const now = new Date();
    const clockEl = $('digitalClock');
    const dateEl = $('digitalDate');
    if (clockEl) clockEl.textContent = now.toTimeString().split(' ')[0];
    if (dateEl) {
      const yr = now.getFullYear();
      const mo = String(now.getMonth() + 1).padStart(2, '0');
      const da = String(now.getDate()).padStart(2, '0');
      dateEl.textContent = `${yr}/${mo}/${da}`;
    }
  }
  setInterval(update, 1000);
  update();
}

// ── KPI Counter Updates ──────────────────────────────────────────────────
function updateKPIs(stats) {
  if (!stats) return;
  if (stats.active_cameras !== undefined) {
    const el = $('kpi-active-cameras');
    if (el) el.textContent = stats.active_cameras;
    const sysTxt = $('sysStatusText');
    if (sysTxt) sysTxt.textContent = `SYSTEM ONLINE · ${stats.active_cameras} CCTV NODES ACTIVE`;
  }
  if (stats.total_detections !== undefined) {
    totalDetectionsCount = Math.max(totalDetectionsCount, stats.total_detections);
    const el = $('kpi-vehicles-detected');
    if (el) el.textContent = totalDetectionsCount.toLocaleString();
  }
  if (stats.total_vehicles !== undefined) {
    const totalVeh = Math.max(knownVehicles.size, stats.total_vehicles);
    const el = $('kpi-unique-vehicles');
    if (el) el.textContent = totalVeh.toLocaleString();
  }
  if (stats.total_plates !== undefined) {
    const totalPlt = Math.max(knownPlates.size, stats.total_plates);
    const el = $('kpi-plates-recognized');
    if (el) el.textContent = totalPlt.toLocaleString();
  }
  if (stats.cross_matches !== undefined) {
    crossEventsCount = Math.max(crossEventsCount, stats.cross_matches);
    const el = $('kpi-cross-matches');
    if (el) el.textContent = crossEventsCount.toLocaleString();
    const badge = $('crossEventBadge');
    if (badge) badge.textContent = `${crossEventsCount} TRANSITIONS`;
  }
}

// ── Camera Telemetry Updates ─────────────────────────────────────────────
function updateCameraHud(cameras) {
  if (!cameras) return;
  Object.values(cameras).forEach((cam) => {
    const cid = cam.id;
    const locEl = $(`loc-${cid}`);
    const statsEl = $(`camStats-${cid}`);
    const telVeh = $(`telVeh-${cid}`);
    const telAnpr = $(`telAnpr-${cid}`);
    const telConf = $(`telConf-${cid}`);

    if (locEl && cam.location) locEl.textContent = cam.location;
    if (statsEl) {
      const res = cam.resolution || '1280x720';
      const fps = (cam.fps || 24.0).toFixed(1);
      statsEl.textContent = `${res} · ${fps} FPS`;
    }
    if (telVeh) telVeh.textContent = cam.vehicles_current ?? 0;
    if (telAnpr) telAnpr.textContent = cam.anpr_count ?? 0;
    if (telConf) telConf.textContent = cam.ai_confidence ? `${cam.ai_confidence.toFixed(1)}%` : '—';
  });
}

// ── Cross-Camera Transition Feed ──────────────────────────────────────────
function addCrossCameraEvent(ev) {
  const feed = $('transitionsFeed');
  if (!feed) return;
  const empty = $('feedEmptyState');
  if (empty) empty.remove();

  const evKey = (ev.id ? 'id_' + ev.id : '') || `${ev.timestamp || ''}_${ev.global_id || ''}_${ev.from_camera || ''}_${ev.to_camera || ''}`;
  if (seenTransitionIds.has(evKey)) return;
  seenTransitionIds.add(evKey);
  if (seenTransitionIds.size > 1000) {
    const it = seenTransitionIds.values();
    for (let i = 0; i < 200; i++) seenTransitionIds.delete(it.next().value);
  }

  // Deduplicate DOM by ID if already present
  if (ev.id && document.getElementById(`trans-card-${ev.id}`)) {
    return;
  }

  const card = document.createElement('div');
  card.className = 'trans-card';
  card.id = `trans-card-${ev.id || Date.now()}`;

  const gid = ev.global_id || 'VEH_GLOBAL_????';
  const fromCam = ev.from_camera || 'CAM_A';
  const toCam = ev.to_camera || 'CAM_B';
  const plate = ev.plate && ev.plate !== 'UNKNOWN' ? ev.plate : 'PLATE UNKNOWN';
  const isPlateKnown = ev.plate && ev.plate !== 'UNKNOWN';
  const vtype = ev.vehicle_type || 'Vehicle';
  const color = ev.color || 'Unknown';
  const timeStr = ev.timestamp ? (ev.timestamp.split('T')[1] || ev.timestamp).split('.')[0] : new Date().toLocaleTimeString();

  card.innerHTML = `
    <div class="trans-top">
      <div class="trans-veh-id">
        <span class="trans-badge-glow">MATCH</span>
        <span>${gid}</span>
      </div>
      <span class="trans-time">${timeStr}</span>
    </div>
    <div class="trans-route">
      <span class="route-cam">${fromCam}</span>
      <span class="route-arrow">➔</span>
      <span class="route-cam">${toCam}</span>
      <span style="color:var(--text-dim); font-size:10px; margin-left:auto;">${vtype} (${color})</span>
    </div>
    <div class="trans-meta">
      <span class="plate-pill ${isPlateKnown ? 'active' : 'unknown'}">${plate}</span>
      <span style="color:var(--text-dim); margin-left:auto; font-size:10px;">CLICK TO INSPECT ROUTE</span>
    </div>
  `;

  card.onclick = () => openVehicleModal(gid);
  feed.insertBefore(card, feed.firstChild);

  while (feed.children.length > 50) {
    feed.removeChild(feed.lastChild);
  }

  crossEventsCount++;
  const badge = $('crossEventBadge');
  if (badge) badge.textContent = `${crossEventsCount} TRANSITIONS`;
  const kpiMatches = $('kpi-cross-matches');
  if (kpiMatches) kpiMatches.textContent = crossEventsCount.toLocaleString();
}

// ── Real-Time Detection Table ────────────────────────────────────────────
function addDetectionRow(d) {
  const tbody = $('detectionTableBody');
  if (!tbody) return;

  const detKey = `${d.timestamp || ''}_${d.camera_id || ''}_${d.local_id || ''}_${d.global_id || ''}`;
  if (seenDetectionKeys.has(detKey)) return;
  seenDetectionKeys.add(detKey);
  if (seenDetectionKeys.size > 2000) {
    const it = seenDetectionKeys.values();
    for (let i = 0; i < 400; i++) seenDetectionKeys.delete(it.next().value);
  }

  const tr = document.createElement('tr');
  const timeStr = d.timestamp ? (d.timestamp.split('T')[1] || d.timestamp).split('.')[0] : new Date().toLocaleTimeString();
  const camId = d.camera_id || 'CAM';
  const localId = d.local_id || '—';
  const globalId = d.global_id || d.vehicle_id || '—';
  const vtype = d.vehicle_type || 'Vehicle';
  const color = d.color || 'Unknown';
  const plate = d.number_plate || 'UNKNOWN';
  const isPlateKnown = plate !== 'UNKNOWN' && plate !== '' && plate !== 'NONE';
  const conf = Math.round(d.detection_confidence || (d.confidence ? d.confidence * 100 : 0));

  tr.innerHTML = `
    <td class="td-mono">${timeStr}</td>
    <td><span class="cam-tag">${camId}</span></td>
    <td class="td-mono loc-id-tag">${localId}</td>
    <td class="td-mono gbl-id-tag">${globalId}</td>
    <td>${vtype}</td>
    <td>${color}</td>
    <td><span class="plate-pill ${isPlateKnown ? 'active' : 'unknown'}">${plate}</span></td>
    <td class="conf-bar-cell">${conf}%</td>
  `;

  tr.onclick = () => openVehicleModal(globalId);

  // Search filter caching
  tr.dataset.search = `${timeStr} ${camId} ${localId} ${globalId} ${vtype} ${color} ${plate}`.toLowerCase();
  const filterInput = $('eventTableSearch');
  const filterVal = filterInput ? (filterInput.value || '').trim().toLowerCase() : '';
  if (filterVal && !tr.dataset.search.includes(filterVal)) {
    tr.style.display = 'none';
  }

  tbody.insertBefore(tr, tbody.firstChild);

  while (tbody.children.length > 150) {
    tbody.removeChild(tbody.lastChild);
  }

  // Update KPI counters
  totalDetectionsCount++;
  if (globalId && globalId !== '—') knownVehicles.add(globalId);
  if (isPlateKnown) knownPlates.add(plate);

  const kpiDet = $('kpi-vehicles-detected');
  if (kpiDet) kpiDet.textContent = totalDetectionsCount.toLocaleString();
  const kpiVeh = $('kpi-unique-vehicles');
  if (kpiVeh) kpiVeh.textContent = knownVehicles.size.toLocaleString();
  const kpiPlt = $('kpi-plates-recognized');
  if (kpiPlt) kpiPlt.textContent = knownPlates.size.toLocaleString();
}

// Table Search Filtering
function initSearchFilter() {
  const searchInput = $('eventTableSearch');
  if (!searchInput) return;
  searchInput.addEventListener('input', (e) => {
    const query = e.target.value.trim().toLowerCase();
    const rows = $('detectionTableBody') ? $('detectionTableBody').querySelectorAll('tr') : [];
    rows.forEach((r) => {
      if (!query || (r.dataset.search && r.dataset.search.includes(query))) {
        r.style.display = '';
      } else {
        r.style.display = 'none';
      }
    });
  });
}

// ── VEHICLE IDENTITY DOSSIER MATRIX (IDENTITY CARDS) ──────────────────────
function renderIdentityCards(vehicles) {
  const container = $('identityCardsGrid');
  if (!container) return;

  const registryBadge = $('idRegistryCount');
  if (registryBadge) {
    registryBadge.textContent = `${vehicles.length} VEHICLES ENROLLED`;
  }

  // Apply filters
  const q = idSearchQuery.trim().toLowerCase();
  const filtered = vehicles.filter(v => {
    // 1. Text search
    if (q) {
      const searchStr = `${v.vehicle_id || ''} ${v.number_plate || ''} ${v.vehicle_type || ''} ${v.color || ''} ${(v.cameras_seen || []).join(' ')}`.toLowerCase();
      if (!searchStr.includes(q)) return false;
    }

    // 2. Chip filter
    const plate = v.number_plate || '';
    const hasPlate = plate !== 'UNKNOWN' && plate !== '' && plate !== 'NONE';
    const vtype = (v.vehicle_type || '').toLowerCase();
    const cams = v.cameras_seen || [];

    if (activeIdFilter === 'anpr') return hasPlate;
    if (activeIdFilter === 'multicam') return cams.length >= 2;
    if (activeIdFilter === 'car') return vtype === 'car';
    if (activeIdFilter === 'truck') return vtype.includes('truck') || vtype.includes('bus');
    if (activeIdFilter === 'bike') return vtype.includes('motorcycle') || vtype.includes('bike') || vtype.includes('bicycle');
    return true;
  });

  if (filtered.length === 0) {
    container.innerHTML = `<div class="id-cards-empty">No vehicle identity profiles match the active search or filter.</div>`;
    return;
  }

  container.innerHTML = filtered.map(v => {
    const vid = v.vehicle_id || 'VEH_GLOBAL_????';
    const plate = v.number_plate || 'UNKNOWN';
    const isPlateKnown = plate !== 'UNKNOWN' && plate !== '' && plate !== 'NONE';
    const vtype = v.vehicle_type || 'Vehicle';
    const color = v.color || 'Unknown';
    const colorHex = getColorHex(color);
    const cams = v.cameras_seen || [];
    const sightings = v.frames_tracked || 1;
    const lastSeen = v.last_seen ? (v.last_seen.split('T')[1] || v.last_seen).split('.')[0] : 'Just now';

    return `
      <div class="id-card" onclick="openVehicleModal('${vid}')">
        <div class="id-card-top">
          <div class="id-card-gid">
            <span class="id-status-badge ${isPlateKnown ? 'verified' : 'reid'}">${isPlateKnown ? 'VERIFIED ANPR' : 'GLOBAL RE-ID'}</span>
            <b>${vid}</b>
          </div>
          <span class="id-sightings-tag">Seen ${sightings}x</span>
        </div>

        <div class="id-card-body">
          <div class="id-visual-row">
            <div class="id-img-box">
              <img src="/output/vehicle_crops/${encodeURIComponent(vid)}.jpg"
                   alt="${vid}"
                   loading="lazy"
                   onerror="this.parentElement.innerHTML='<div class=\'id-no-img\'>PHOTO PENDING</div>';">
            </div>
            <div class="id-plate-box">
              <div class="plate-embossed ${isPlateKnown ? 'active' : 'scanning'}">
                <span class="anpr-header">IND · ANPR BADGE</span>
                <span class="plate-val">${isPlateKnown ? plate : 'ANPR SCANNING...'}</span>
              </div>
            </div>
          </div>

          <div class="id-meta-grid">
            <div class="id-meta-item">
              <span class="id-meta-label">CLASSIFICATION</span>
              <b class="id-meta-val">${vtype}</b>
            </div>
            <div class="id-meta-item">
              <span class="id-meta-label">COLOR SPEC</span>
              <b class="id-meta-val"><span class="color-dot" style="background:${colorHex}"></span>${color}</b>
            </div>
            <div class="id-meta-item">
              <span class="id-meta-label">CAMERAS LOGGED</span>
              <b class="id-meta-val cyan-text">${cams.length} Surveillance Nodes</b>
            </div>
            <div class="id-meta-item">
              <span class="id-meta-label">LAST SIGHTED</span>
              <b class="id-meta-val">${lastSeen}</b>
            </div>
          </div>

          <div class="id-route-flow">
            ${cams.length > 0 ? cams.map(cam => `<span class="id-route-pill">${cam}</span>`).join('<span class="id-arrow">➔</span>') : '<span style="color:var(--text-dim); font-size:9px;">Single camera transit</span>'}
          </div>
        </div>

        <div class="id-card-foot">
          <span>INSPECT TRAJECTORY & SIGHTING LOGS</span>
          <span class="id-arrow-btn">➔</span>
        </div>
      </div>
    `;
  }).join('');
}

// Initialize Identity Toolbar Filter & Search Listeners
function initIdentityToolbar() {
  const searchInput = $('idCardSearch');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      idSearchQuery = e.target.value;
      renderIdentityCards(allRegisteredVehicles);
    });
  }

  const chips = document.querySelectorAll('.id-chip');
  chips.forEach(chip => {
    chip.addEventListener('click', () => {
      chips.forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      activeIdFilter = chip.dataset.filter || 'all';
      renderIdentityCards(allRegisteredVehicles);
    });
  });
}

// ── Vehicle Detail Modal ─────────────────────────────────────────────────
async function openVehicleModal(vehicleId) {
  const modal = $('vehModal');
  const title = $('modalTitle');
  const body = $('modalBody');
  if (!modal || !title || !body) return;

  title.textContent = `VEHICLE INTEL DOSSIER: ${vehicleId}`;
  body.innerHTML = `<div style="text-align:center; padding:20px; color:var(--text-dim);">Loading vehicle profile dossier...</div>`;
  modal.classList.add('show');

  try {
    const res = await fetch(`/api/vehicles/${encodeURIComponent(vehicleId)}`);
    if (!res.ok) throw new Error('Vehicle not found');
    const data = await res.json();
    const v = data.vehicle || {};
    const sightings = data.sightings || [];

    const plate = v.number_plate || 'UNKNOWN';
    const isPlateKnown = plate !== 'UNKNOWN' && plate !== '' && plate !== 'NONE';

    body.innerHTML = `
      <div style="display:flex; gap:14px; margin-bottom:14px; align-items:center; justify-content:center; flex-wrap:wrap;">
        <div style="text-align:center;">
          <img src="/output/vehicle_crops/${encodeURIComponent(v.vehicle_id || vehicleId)}.jpg"
               style="max-height:120px; max-width:200px; border-radius:6px; border:1px solid var(--cyan); object-fit:cover; box-shadow:0 4px 16px rgba(0,0,0,0.5);"
               onerror="this.style.display='none'">
        </div>
        ${isPlateKnown ? `
          <div style="text-align:center;">
            <div style="padding:10px 16px; background:linear-gradient(135deg, #092117 0%, #06150e 100%); border:1.5px solid var(--emerald); border-radius:6px; box-shadow:0 0 16px var(--emerald-glow);">
              <div style="font-size:9px; color:var(--emerald); letter-spacing:1.5px; font-weight:800; margin-bottom:2px;">ANPR VERIFIED LICENSE PLATE</div>
              <div style="font-family:var(--font-mono); font-size:20px; font-weight:800; color:#00ff88; letter-spacing:2px;">${plate}</div>
            </div>
          </div>
        ` : ''}
      </div>

      <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:14px; background:#07101d; padding:12px; border-radius:6px; border:1px solid var(--border-subtle);">
        <div><span style="color:var(--text-dim); font-size:10px;">GLOBAL ID:</span> <b class="purple-text" style="font-family:var(--font-mono);">${v.vehicle_id || vehicleId}</b></div>
        <div><span style="color:var(--text-dim); font-size:10px;">PLATE:</span> <b class="emerald-text" style="font-family:var(--font-mono);">${plate}</b></div>
        <div><span style="color:var(--text-dim); font-size:10px;">TYPE / COLOR:</span> <b>${v.vehicle_type || '—'} · ${v.color || '—'}</b></div>
        <div><span style="color:var(--text-dim); font-size:10px;">TOTAL DETECTIONS:</span> <b class="cyan-text">${v.frames_tracked || 1} frames</b></div>
        <div><span style="color:var(--text-dim); font-size:10px;">FIRST SEEN:</span> <b>${v.first_seen || '—'}</b></div>
        <div><span style="color:var(--text-dim); font-size:10px;">LAST SEEN:</span> <b>${v.last_seen || '—'}</b></div>
        <div style="grid-column:1 / -1;"><span style="color:var(--text-dim); font-size:10px;">TRAVERSED NODES:</span> <b class="cyan-text">${(v.cameras_seen || []).join('  ➔  ') || '—'}</b></div>
      </div>

      <div style="font-weight:800; color:var(--cyan); margin-bottom:8px; font-size:12px; letter-spacing:1px;">
        CROSS-CAMERA SIGHTINGS & TRAJECTORY (${sightings.length} SURVEILLANCE EVENTS)
      </div>
      <div style="display:flex; flex-direction:column; gap:6px; max-height:200px; overflow-y:auto; padding-right:4px;">
        ${sightings.map(s => `
          <div style="display:flex; justify-content:space-between; align-items:center; background:#0d182b; border-left:3px solid var(--cyan); padding:8px 12px; border-radius:4px; font-size:11px;">
            <div>
              <b class="cyan-text">${s.camera_id}</b>
              <span style="color:var(--text-muted); margin-left:8px;">${s.camera_location || ''}</span>
            </div>
            <div style="font-family:var(--font-mono); color:var(--text-dim); font-size:10px;">
              Seen ${s.sightings_count || 1}x · ${s.last_seen ? s.last_seen.split('T')[1] || s.last_seen : ''}
            </div>
          </div>
        `).join('') || '<div style="color:var(--text-dim); padding:8px;">No previous sightings.</div>'}
      </div>
    `;
  } catch (err) {
    body.innerHTML = `<div style="color:var(--rose); padding:20px;">Could not load vehicle dossier: ${err.message}</div>`;
  }
}

function closeModal() {
  const modal = $('vehModal');
  if (modal) modal.classList.remove('show');
}

// ── Alert Toasts ─────────────────────────────────────────────────────────
function showToast(msg) {
  const stack = $('toastStack');
  if (!stack) return;
  const toast = document.createElement('div');
  toast.className = 'toast-item';
  toast.textContent = msg;
  stack.appendChild(toast);
  setTimeout(() => toast.remove(), 5000);
}

// ── High-Speed Auto-Sync Polling Engine ───────────────────────────────────
let isSyncing = false;
let lastVehiclesFetch = 0;

async function syncAllData() {
  if (isSyncing) return;
  isSyncing = true;
  try {
    // 1. Status & KPIs & Cameras
    const statusRes = await fetch('/api/status');
    if (statusRes.ok) {
      const statusData = await statusRes.json();
      updateKPIs(statusData.stats);
      updateCameraHud(statusData.cameras);
    }

    // 2. Recent Vehicle Detections (Event Log Table)
    const detRes = await fetch('/api/detections/recent');
    if (detRes.ok) {
      const detData = await detRes.json();
      const dets = detData.detections || [];
      dets.slice().reverse().forEach(d => addDetectionRow(d));
    }

    // 3. Cross-Camera Transition Events
    const crossRes = await fetch('/api/cross_events');
    if (crossRes.ok) {
      const crossData = await crossRes.json();
      const evs = crossData.events || [];
      evs.slice().reverse().forEach(ev => addCrossCameraEvent(ev));
    }

    // 4. Vehicle Identity Dossier Matrix (Every 2 seconds)
    const now = Date.now();
    if (now - lastVehiclesFetch > 2000) {
      lastVehiclesFetch = now;
      const vehRes = await fetch('/api/vehicles');
      if (vehRes.ok) {
        const vehData = await vehRes.json();
        const vehicles = vehData.vehicles || [];
        if (vehicles.length !== allRegisteredVehicles.length || JSON.stringify(vehicles[0]) !== JSON.stringify(allRegisteredVehicles[0])) {
          allRegisteredVehicles = vehicles;
          renderIdentityCards(allRegisteredVehicles);
        }
      }
    }
  } catch (e) {
    console.warn('[SENTINEL] Sync error:', e);
  } finally {
    isSyncing = false;
  }
}

// ── Socket.IO Event Handlers (If active) ──────────────────────────────────
if (socket) {
  socket.on('connect', () => {
    console.log('[SENTINEL] Connected to command center WebSocket.');
    syncAllData();
  });

  socket.on('detection', (payload) => {
    const dets = payload.detections || [];
    dets.forEach(d => addDetectionRow(d));
  });

  socket.on('cross_camera_event', (ev) => {
    addCrossCameraEvent(ev);
    showToast(`CROSS-CAMERA MATCH: ${ev.global_id} (${ev.from_camera} → ${ev.to_camera})`);
  });

  socket.on('alert', (a) => {
    showToast(`WATCHLIST ALERT: Plate ${a.plate} at ${a.location}`);
  });
}

// Active auto-sync interval (every 500ms for instant real-time updates)
setInterval(syncAllData, 500);

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  initClock();
  initSearchFilter();
  initIdentityToolbar();
  syncAllData();
});
