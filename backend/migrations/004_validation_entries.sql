-- Migration 004: Add validation_entries table for R2
-- Migrates validation study data from flat-file to Supabase-backed storage.

CREATE TABLE IF NOT EXISTS validation_entries (
    id TEXT PRIMARY KEY,
    video_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    analysis_type TEXT NOT NULL,
    predicted_scores JSONB NOT NULL,
    actual_views INTEGER NOT NULL,
    actual_engagement REAL NOT NULL,
    would_publish BOOLEAN NOT NULL DEFAULT TRUE,
    days_after_publish INTEGER NOT NULL DEFAULT 7,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_validation_entries_user_id ON validation_entries(user_id);
CREATE INDEX IF NOT EXISTS idx_validation_entries_submitted_at ON validation_entries(submitted_at DESC);

ALTER TABLE validation_entries ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist (idempotent)
DROP POLICY IF EXISTS "Users can read own validation_entries" ON validation_entries;
DROP POLICY IF EXISTS "Users can insert own validation_entries" ON validation_entries;
DROP POLICY IF EXISTS "Users can delete own validation_entries" ON validation_entries;

-- All authenticated users can read all entries (needed for cross-user study computation)
CREATE POLICY "Users can read all validation_entries"
    ON validation_entries FOR SELECT
    USING (auth.uid() IS NOT NULL);

CREATE POLICY "Users can insert own validation_entries"
    ON validation_entries FOR INSERT
    WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Users can delete own validation_entries"
    ON validation_entries FOR DELETE
    USING (auth.uid()::text = user_id);
