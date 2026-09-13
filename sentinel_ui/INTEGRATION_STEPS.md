# Exact integration into sentinel-gujarat-cctv-platform

I inspected the public repository before creating this patch.

## Existing structure

The repo is a React/Vite application with routes including:
- `/live-cameras`
- `/vehicle-tracking`
- `/alerts`
- `/gis`
- `/event-search`

The existing vehicle page calls `searchVehicleByPlate()` and `getRecentVehicleMovements()`, but that service currently uses `mockVehiclesDatabase` and `mockRecentMovements`.

The existing database schema already has cameras and ANPR detections. This patch therefore adds an additive `ai_detections` table.

## Step 1 — Copy files

Copy:
- `ai-service/` -> repo root `ai-service/`
- `src/services/liveAiService.js` -> repo `src/services/`
- `src/components/ai/LiveAiFeed.jsx` -> repo `src/components/ai/`
- `server/database/ai_detections.sql` -> repo `server/database/`

## Step 2 — Database

Use the SAME DATABASE_URL as the existing project.

Run:
`server/database/ai_detections.sql`

The Python service also creates this table automatically if DATABASE_URL is configured.

## Step 3 — Python AI

From `ai-service`:
`pip install -r requirements.txt`
`uvicorn main:app --host 0.0.0.0 --port 8100`

## Step 4 — Frontend

Add to `.env`:
`VITE_AI_API_URL=http://127.0.0.1:8100`

Import:
`import LiveAiFeed from '../components/ai/LiveAiFeed';`

Then place:
`<LiveAiFeed cameraId={selectedCamera?.id} />`

inside `LiveCameras.jsx` below the VideoPlayer.

## Step 5 — Start AI

Call:
`POST http://127.0.0.1:8100/start`

Body:
`{"camera_id":"CAM-001","stream_url":"YOUR_AUTHORIZED_RTSP_URL"}`

## Step 6 — Replace mock vehicle feed

In `src/services/vehicleService.js`, the next integration step is to replace the mock database functions with calls to the backend/AI detection API. Do this after confirming the live feed is working.

## Why this is separate

The browser should not run YOLO on the CCTV stream. The Python AI worker handles RTSP/video + inference, while React remains responsible for the command-room UI. This keeps the current website intact and gives you a real live-data path.

## Current limitation

I cannot push directly to the GitHub repository from this chat. This patch is prepared against the public repo structure; if you upload the repository ZIP here, I can merge these files into the actual repo and return one ready-to-run ZIP.
