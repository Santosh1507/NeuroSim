-- NeuroSim Database Schema
-- Run in Supabase SQL Editor

CREATE TABLE IF NOT EXISTS videos (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL DEFAULT 'anonymous',
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
    user_id TEXT NOT NULL DEFAULT 'anonymous',
    data JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_analyses_video_id ON analyses(video_id);
CREATE INDEX IF NOT EXISTS idx_videos_upload_time ON videos(upload_time DESC);
CREATE INDEX IF NOT EXISTS idx_videos_user_id ON videos(user_id);

ALTER TABLE videos ENABLE ROW LEVEL SECURITY;
ALTER TABLE analyses ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow all access" ON videos;
DROP POLICY IF EXISTS "Allow all access" ON analyses;

CREATE POLICY "Users can read own videos"
    ON videos FOR SELECT
    USING (auth.uid()::text = user_id OR auth.uid() IS NULL);

CREATE POLICY "Users can insert own videos"
    ON videos FOR INSERT
    WITH CHECK (auth.uid()::text = user_id OR user_id = 'anonymous');

CREATE POLICY "Users can update own videos"
    ON videos FOR UPDATE
    USING (auth.uid()::text = user_id)
    WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Users can delete own videos"
    ON videos FOR DELETE
    USING (auth.uid()::text = user_id);

CREATE POLICY "Users can read own analyses"
    ON analyses FOR SELECT
    USING (auth.uid()::text = user_id OR auth.uid() IS NULL);

CREATE POLICY "Users can insert own analyses"
    ON analyses FOR INSERT
    WITH CHECK (auth.uid()::text = user_id OR user_id = 'anonymous');

CREATE POLICY "Users can delete own analyses"
    ON analyses FOR DELETE
    USING (auth.uid()::text = user_id);
