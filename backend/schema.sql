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
CREATE INDEX IF NOT EXISTS idx_analyses_user_id ON analyses(user_id);
CREATE INDEX IF NOT EXISTS idx_videos_upload_time ON videos(upload_time DESC);
CREATE INDEX IF NOT EXISTS idx_videos_user_id ON videos(user_id);

ALTER TABLE videos ENABLE ROW LEVEL SECURITY;
ALTER TABLE analyses ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow all access" ON videos;
DROP POLICY IF EXISTS "Allow all access" ON analyses;

CREATE POLICY "Users can read own videos"
    ON videos FOR SELECT
    USING (
        (auth.uid() IS NULL AND user_id = 'anonymous')
        OR (auth.uid() IS NOT NULL AND auth.uid()::text = user_id)
    );

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
    USING (
        (auth.uid() IS NULL AND user_id = 'anonymous')
        OR (auth.uid() IS NOT NULL AND auth.uid()::text = user_id)
    );

CREATE POLICY "Users can insert own analyses"
    ON analyses FOR INSERT
    WITH CHECK (auth.uid()::text = user_id OR user_id = 'anonymous');

CREATE POLICY "Users can delete own analyses"
    ON analyses FOR DELETE
    USING (auth.uid()::text = user_id);

CREATE TABLE IF NOT EXISTS ab_tests (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL DEFAULT 'anonymous',
    name TEXT NOT NULL,
    baseline_video_id TEXT NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    variant_video_id TEXT REFERENCES videos(id) ON DELETE SET NULL,
    variant_script TEXT,
    results JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ab_tests_user_id ON ab_tests(user_id);

ALTER TABLE ab_tests ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow all access" ON ab_tests;

CREATE POLICY "Users can read own ab_tests"
    ON ab_tests FOR SELECT
    USING (
        (auth.uid() IS NULL AND user_id = 'anonymous')
        OR (auth.uid() IS NOT NULL AND auth.uid()::text = user_id)
    );

CREATE POLICY "Users can insert own ab_tests"
    ON ab_tests FOR INSERT
    WITH CHECK (auth.uid()::text = user_id OR user_id = 'anonymous');

CREATE POLICY "Users can delete own ab_tests"
    ON ab_tests FOR DELETE
    USING (auth.uid()::text = user_id);

CREATE TABLE IF NOT EXISTS waitlist (
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    queue_position INT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE waitlist ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow public insert to waitlist" ON waitlist;
DROP POLICY IF EXISTS "Allow admin read waitlist" ON waitlist;

CREATE POLICY "Allow public insert to waitlist"
    ON waitlist FOR INSERT
    WITH CHECK (true);

CREATE POLICY "Allow admin read waitlist"
    ON waitlist FOR SELECT
    USING (auth.uid() IS NOT NULL);

CREATE TABLE IF NOT EXISTS social_simulations (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL DEFAULT 'anonymous',
    video_id TEXT NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    platform TEXT NOT NULL,
    algorithmic_score REAL NOT NULL,
    vtr REAL NOT NULL,
    retention_data JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_social_simulations_user_id ON social_simulations(user_id);

ALTER TABLE social_simulations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own social_simulations"
    ON social_simulations FOR SELECT
    USING (
        (auth.uid() IS NULL AND user_id = 'anonymous')
        OR (auth.uid() IS NOT NULL AND auth.uid()::text = user_id)
    );

CREATE POLICY "Users can insert own social_simulations"
    ON social_simulations FOR INSERT
    WITH CHECK (auth.uid()::text = user_id OR user_id = 'anonymous');

CREATE POLICY "Users can delete own social_simulations"
    ON social_simulations FOR DELETE
    USING (auth.uid()::text = user_id);


