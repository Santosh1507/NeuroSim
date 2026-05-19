CREATE TABLE IF NOT EXISTS share_links (
    id TEXT PRIMARY KEY,
    video_id TEXT REFERENCES videos(id) ON DELETE CASCADE,
    created_by TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    allow_download BOOLEAN DEFAULT true,
    allow_embed BOOLEAN DEFAULT false
);

CREATE INDEX IF NOT EXISTS idx_share_links_video_id ON share_links(video_id);
CREATE INDEX IF NOT EXISTS idx_share_links_expires_at ON share_links(expires_at);

ALTER TABLE share_links ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Anyone can read active share links" ON share_links FOR SELECT USING (expires_at IS NULL OR expires_at > NOW());
