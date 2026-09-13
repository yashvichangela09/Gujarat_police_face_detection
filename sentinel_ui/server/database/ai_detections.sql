-- Additive table. Existing cameras/ANPR/events/alerts schema remains unchanged.
CREATE TABLE IF NOT EXISTS ai_detections (
  id BIGSERIAL PRIMARY KEY,
  camera_id VARCHAR(64),
  detection_type VARCHAR(32) NOT NULL, -- vehicle | face
  label VARCHAR(128),
  confidence NUMERIC(7,5),
  bbox JSONB,
  track_id INTEGER,
  plate_number VARCHAR(64),
  captured_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_ai_detections_camera_time
  ON ai_detections(camera_id, captured_at);
CREATE INDEX IF NOT EXISTS idx_ai_detections_type
  ON ai_detections(detection_type);
