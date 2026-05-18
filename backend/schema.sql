-- NeuroSim Database Schema
-- Run in Supabase SQL Editor

CREATE TABLE IF NOT EXISTS videos (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'uploaded',
    upload_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    duration FLOAT,
    transcript TEXT,
    file_path TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS analyses (
    id TEXT PRIMARY KEY,
    video_id TEXT NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    data JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_analyses_video_id ON analyses(video_id);
CREATE INDEX IF NOT EXISTS idx_videos_upload_time ON videos(upload_time DESC);

-- Enable Row Level Security (optional - disable for now)
ALTER TABLE videos ENABLE ROW LEVEL SECURITY;
ALTER TABLE analyses ENABLE ROW LEVEL SECURITY;

-- Allow public read/write for now (add auth policies later)
CREATE POLICY "Allow all access" ON videos FOR ALL USING (true);
CREATE POLICY "Allow all access" ON analyses FOR ALL USING (true);
