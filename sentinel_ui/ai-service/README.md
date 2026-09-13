# SENTINEL AI Live Integration

This is a drop-in AI microservice for the existing SENTINEL React/Node/PostgreSQL project.

## What I found in the repository

The existing project already has:
- React/Vite frontend and a `/vehicle-tracking` page.
- A camera service with live catalogue/RTSP/HLS/WebRTC fields.
- PostgreSQL schema containing `cameras`, `anpr_detections`, `alerts`, `events`, and `audit_logs`.
- Existing vehicle tracking currently reads from `mockVehicles` rather than live AI data.

This patch adds a separate Python AI process rather than replacing your current website.

## Run

1. Copy `.env.example` to `.env` and put the SAME DATABASE_URL used by the existing backend.
2. Install:
   `pip install -r requirements.txt`
3. Start:
   `uvicorn main:app --host 0.0.0.0 --port 8100`
4. In the React app set:
   `VITE_AI_API_URL=http://127.0.0.1:8100`
5. Start AI for an authorized camera by POSTing `/start` with its RTSP URL.

Example:
```json
{"camera_id":"CAM-001","stream_url":"rtsp://USER:PASSWORD@CAMERA_IP:554/stream"}
```

## Real-data demo

Use an RTSP/HLS source that you are authorized to process. The AI worker reads the live stream, runs YOLO vehicle detection/tracking and OpenCV face detection, writes real detection events to PostgreSQL, and pushes new events over WebSocket.

For a hackathon demo, start 1–3 cameras first. Running 30 HD streams through YOLO on one laptop will usually overload it.

## Face

The face component is detection only. It does not perform identity recognition or matching.

## Existing schema

The patch intentionally adds a separate `ai_detections` table so your current `anpr_detections` schema is not broken. Once your real ANPR/OCR output is ready, map confirmed plate reads into the existing `anpr_detections` table.

## Important

Do not hard-code camera passwords or database credentials into Git. Use `.env`/secrets and only process camera streams for which you have authorization.
