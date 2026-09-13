# Gujarat Police Real-Time AI Face & Vehicle Intelligence Command Center 🚨

A comprehensive, multi-camera AI surveillance system designed for real-time CCTV monitoring, license plate ANPR OCR recognition, cross-camera vehicle tracking Re-ID, and InsightFace deep learning facial recognition.

---

## 🌟 Key Features

### 1. 👤 Real-Time InsightFace Facial Recognition
- **Watchlist Suspect Identification**: Compares live CCTV camera feeds against stored watchlist target embeddings (`known_faces`) using Cosine Similarity matching.
- **WANTED Alerts**: Automatically triggers high-visibility **RED HUD Alerts (`🚨 WANTED: <Suspect Name>`)** with FIR registered details when a suspect is detected.
- **Normal Citizen Classification**: Classifies non-watchlist individuals cleanly as **`👤 CITIZEN: CLEAR`** in emerald green without false positive alarms.

### 2. 🚘 Multi-Camera Vehicle Intelligence (YOLOv11 + ANPR)
- **High-Performance Detection**: YOLOv11 deep learning model tracking cars, buses, trucks, motorcycles, and auto-rickshaws.
- **License Plate OCR**: Fine-tuned license plate detection and OCR text extraction.
- **Cross-Camera Re-ID**: Tracks global vehicle movements across multiple camera locations.

### 3. 🖥️ Command Center Web Dashboard (React + Vite + Tailwind CSS)
- **Multi-Camera Matrix View**: Supports 1x1, 2x2, and full grid live MJPEG video streams.
- **Live Event Log & Search**: Search vehicles by number plate and suspects by face trail.
- **PTZ Camera Controls**: Simulated pan-tilt-zoom camera tracking.

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.10+
- Node.js 18+

### 1. Backend AI Server Setup (Flask + YOLO + InsightFace)
```bash
cd sentinel_police_ai
pip install -r requirements.txt
pip install insightface onnxruntime
python main.py
```
*Backend runs on `http://127.0.0.1:5000`*

### 2. Frontend Web Command Center Setup (React + Vite)
```bash
cd sentinel_ui
npm install
npm run dev
```
*Frontend runs on `http://localhost:5173`*

---

## ☁️ Deployment on Vercel

The React Web Command Center UI (`sentinel_ui`) is ready for 1-click deployment on [Vercel](https://vercel.com).

1. Connect your GitHub repository: `yashvichangela09/Gujarat_police_face_detection`
2. Set Root Directory to `sentinel_ui`
3. Framework Preset: **Vite**
4. Build Command: `npm run build`
5. Output Directory: `dist`
