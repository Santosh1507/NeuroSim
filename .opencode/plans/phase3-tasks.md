# Phase 3: Growth Infrastructure — Detailed Tasks

## T13: main.py Route Splitting

### Step 1: Create `backend/routes/` package

```
backend/routes/
├── __init__.py
├── upload.py
├── analysis.py
├── share.py
├── premium.py
└── digest.py
```

### Step 2: Extract routes

Each route file follows this pattern:
```python
from fastapi import APIRouter
router = APIRouter(prefix="/api", tags=["name"])

@router.get("/...")
async def endpoint():
    # Move logic from main.py
    pass
```

### Step 3: Update main.py

```python
from routes.upload import router as upload_router
from routes.analysis import router as analysis_router
from routes.share import router as share_router
from routes.premium import router as premium_router
from routes.digest import router as digest_router

app.include_router(upload_router)
app.include_router(analysis_router)
app.include_router(share_router)
app.include_router(premium_router)
app.include_router(digest_router)
```

### Step 4: Verify all tests pass
```bash
cd backend && python -m pytest -v --tb=short
```

### Step 5: Commit
```bash
git add backend/routes/ backend/main.py
git commit -m "refactor: split main.py into route modules"
```

---

## T14: Embed Widget Offline Fallback

### Step 1: Update `frontend/src/app/embed/[id]/page.tsx`

Add:
```tsx
const [isOffline, setIsOffline] = useState(false);

useEffect(() => {
  const fetchAnalysis = async () => {
    try {
      const response = await fetch(`${apiUrl}/api/share/${id}`, { signal: AbortSignal.timeout(5000) });
      if (!response.ok) throw new Error("Failed");
      setAnalysis(await response.json());
    } catch { setIsOffline(true); }
  };
  fetchAnalysis();
}, [id]);

if (isOffline) {
  return (
    <div className="min-h-screen bg-void flex items-center justify-center p-8">
      <div className="glass-panel p-6 max-w-md text-center">
        <div className="w-12 h-12 rounded-full bg-signal-orange/10 flex items-center justify-center mx-auto mb-4">
          <WifiOff className="w-6 h-6 text-signal-orange" />
        </div>
        <h3 className="text-lg font-display font-semibold text-text-primary mb-2">Analysis Unavailable</h3>
        <p className="text-sm text-text-secondary mb-4">The server may be restarting. Please try again in a few minutes.</p>
        <button onClick={() => { setIsOffline(false); window.location.reload(); }} className="btn-ghost text-sm">Retry</button>
      </div>
    </div>
  );
}
```

### Step 2: Commit
```bash
git add frontend/src/app/embed/[id]/page.tsx
git commit -m "feat: add offline fallback to embed widget with retry"
```

---

## T15: Share Link Permissions

### Step 1: Update ShareRequest model in main.py

```python
class ShareRequest(BaseModel):
    video_id: str
    allow_download: bool = True
    allow_embed: bool = False
    expires_in_days: int = 7
```

### Step 2: Update share endpoint

Store permissions in `_share_permissions` dict:
```python
_share_permissions[share_id] = {
    "allow_download": request.allow_download,
    "allow_embed": request.allow_embed,
    "created_by": user_id,
    "created_at": time.time(),
    "expires_at": time.time() + (request.expires_in_days * 86400),
}
```

### Step 3: Create `backend/test_share_permissions.py`

```python
import pytest
from fastapi.testclient import TestClient

class TestSharePermissions:
    def test_create_with_defaults(self):
        from main import app, _share_links, _share_permissions
        _share_links.clear(); _share_permissions.clear()
        client = TestClient(app)
        resp = client.post("/api/share", json={"video_id": "vid_test"}, headers={"authorization": "Bearer dummy"})
        assert resp.status_code == 200
        assert resp.json()["allow_download"] is True
        assert resp.json()["allow_embed"] is False

    def test_create_with_custom(self):
        from main import app, _share_links, _share_permissions
        _share_links.clear(); _share_permissions.clear()
        client = TestClient(app)
        resp = client.post("/api/share", json={"video_id": "vid_test", "allow_download": False, "allow_embed": True},
            headers={"authorization": "Bearer dummy"})
        assert resp.status_code == 200
        assert resp.json()["allow_download"] is False
        assert resp.json()["allow_embed"] is True
```

### Step 4: Run tests
```bash
cd backend && python -m pytest test_share_permissions.py -v
```

### Step 5: Commit
```bash
git add backend/main.py backend/test_share_permissions.py
git commit -m "feat: add share link permissions (download, embed, expiry)"
```

---

## T16: Database Migrations

### Step 1: Create `backend/migrations/001_initial_schema.sql`

```sql
CREATE TABLE IF NOT EXISTS videos (
    id TEXT PRIMARY KEY, user_id TEXT NOT NULL DEFAULT 'anonymous',
    filename TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'uploaded',
    upload_time TIMESTAMPTZ DEFAULT NOW(), duration FLOAT,
    transcript TEXT, file_path TEXT, created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS analyses (
    id TEXT PRIMARY KEY, video_id TEXT REFERENCES videos(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL DEFAULT 'anonymous', data JSONB NOT NULL,
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
```

### Step 2: Create `backend/migrations/002_add_share_links.sql`

```sql
CREATE TABLE IF NOT EXISTS share_links (
    id TEXT PRIMARY KEY, video_id TEXT REFERENCES videos(id) ON DELETE CASCADE,
    created_by TEXT NOT NULL, created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ, allow_download BOOLEAN DEFAULT true, allow_embed BOOLEAN DEFAULT false
);

CREATE INDEX IF NOT EXISTS idx_share_links_video_id ON share_links(video_id);
CREATE INDEX IF NOT EXISTS idx_share_links_expires_at ON share_links(expires_at);

ALTER TABLE share_links ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Anyone can read active share links" ON share_links FOR SELECT USING (expires_at IS NULL OR expires_at > NOW());
```

### Step 3: Create `backend/migrate.py`

```python
import os, sys
from pathlib import Path
from supabase import create_client

def run_migrations():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not url or not key:
        print("SUPABASE_URL and SUPABASE_SERVICE_KEY required"); sys.exit(1)

    supabase = create_client(url, key)
    migrations_dir = Path(__file__).parent / "migrations"

    for migration in sorted(migrations_dir.glob("*.sql")):
        print(f"Applying {migration.name}...")
        sql = migration.read_text()
        try:
            supabase.rpc("exec_sql", {"sql": sql}).execute()
            print(f"  ✓ {migration.name}")
        except Exception as e:
            print(f"  ✗ {migration.name}: {e}"); sys.exit(1)

    print("All migrations applied successfully")

if __name__ == "__main__":
    run_migrations()
```

### Step 4: Commit
```bash
git add backend/migrations/ backend/migrate.py
git commit -m "feat: add database migration system with versioned SQL"
```

---

## T17: CI/CD Auto-Deploy

### Step 1: Update `.github/workflows/ci.yml`

Add after existing jobs:
```yaml
  deploy-backend:
    needs: [backend-tests, frontend-tests]
    if: github.ref == 'refs/heads/master' && github.event_name == 'push'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to Render
        run: |
          curl -X POST "https://api.render.com/v1/services/${{ secrets.RENDER_SERVICE_ID }}/deploys" \
            -H "Authorization: Bearer ${{ secrets.RENDER_API_KEY }}" \
            -H "Content-Type: application/json"

  deploy-frontend:
    needs: [backend-tests, frontend-tests]
    if: github.ref == 'refs/heads/master' && github.event_name == 'push'
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend
    steps:
      - uses: actions/checkout@v4
      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
          cache-dependency-path: frontend/package-lock.json
      - name: Install dependencies
        run: npm ci
      - name: Build
        run: npx next build
      - name: Deploy to Netlify
        uses: nwtgck/actions-netlify@v3
        with:
          publish-dir: ./frontend/out
          production-deploy: true
        env:
          NETLIFY_AUTH_TOKEN: ${{ secrets.NETLIFY_AUTH_TOKEN }}
          NETLIFY_SITE_ID: ${{ secrets.NETLIFY_SITE_ID }}
```

### Step 2: Commit
```bash
git add .github/workflows/ci.yml
git commit -m "ci: add auto-deploy jobs for Render + Netlify"
```

---

## T18: Full Test Suite Verification

### Step 1: Backend
```bash
cd backend && python -m pytest -v --tb=short
```
Expected: 110+ PASS

### Step 2: Frontend
```bash
cd frontend && npx vitest run
```
Expected: 16 PASS

### Step 3: Commit
```bash
git add . && git commit -m "v3.0: growth infrastructure complete"
```
