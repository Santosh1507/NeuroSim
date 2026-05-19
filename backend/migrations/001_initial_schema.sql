CREATE TABLE IF NOT EXISTS videos (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL DEFAULT 'anonymous',
    filename TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'uploaded',
    upload_time TIMESTAMPTZ DEFAULT NOW(),
    duration FLOAT,
    transcript TEXT,
    file_path TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS analyses (
    id TEXT PRIMARY KEY,
    video_id TEXT REFERENCES videos(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL DEFAULT 'anonymous',
    data JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_analyses_video_id ON analyses(video_id);
CREATE INDEX IF NOT EXISTS idx_videos_upload_time ON videos(upload_time);
CREATE INDEX IF NOT EXISTS idx_videos_user_id ON videos(user_id);

ALTER TABLE videos ENABLE ROW LEVEL SECURITY;
ALTER TABLE analyses ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own videos" ON videos FOR SELECT USING (auth.uid()::text = user_id OR user_id = 'anonymous');
CREATE POLICY "Users can insert own videos" ON videos FOR INSERT WITH CHECK (auth.uid()::text = user_id OR user_id = 'anonymous');
CREATE POLICY "Users can read own analyses" ON analyses FOR SELECT USING (auth.uid()::text = user_id OR user_id = 'anonymous');
CREATE POLICY "Users can insert own analyses" ON analyses FOR INSERT WITH CHECK (auth.uid()::text = user_id OR user_id = 'anonymous');
