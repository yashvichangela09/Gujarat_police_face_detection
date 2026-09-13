/**
 * SENTINEL — Live AI bridge to http://127.0.0.1:5000
 */
const DEFAULT_AI_URL = 'http://127.0.0.1:5000';

export const getAiBaseUrl = () =>
  import.meta.env.VITE_AI_API_URL || DEFAULT_AI_URL;

export const startAiForCamera = async (camera) => {
  if (!camera) throw new Error('Camera is required');
  const streamUrl = camera.rtspUrl || camera.rtsp_url;
  const r = await fetch(`${getAiBaseUrl()}/api/status`);
  if (!r.ok) throw new Error(`AI status failed: ${r.status}`);
  return r.json();
};

export const stopAiForCamera = async (cameraId) => {
  return { status: 'ok' };
};

export const getAiDetections = async ({cameraId, limit=100}={}) => {
  const r = await fetch(`${getAiBaseUrl()}/api/detections/recent`);
  if (!r.ok) throw new Error(`AI detections failed: ${r.status}`);
  const data = await r.json();
  return data.detections || [];
};

export const subscribeAiEvents = (onEvent) => {
  const interval = setInterval(async () => {
    try {
      const res = await fetch(`${getAiBaseUrl()}/api/detections/recent`);
      if (res.ok) {
        const data = await res.json();
        if (data.detections && data.detections.length > 0) {
          onEvent(data.detections[0]);
        }
      }
    } catch (e) {}
  }, 1500);

  return () => clearInterval(interval);
};
