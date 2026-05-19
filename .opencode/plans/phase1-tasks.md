# Phase 1: Ship Blockers — Detailed Tasks

## T1: StorageAdapter Tests

### Step 1: Add `_reset()` to StorageAdapter

Add to end of `StorageAdapter` class in `backend/storage_adapter.py`:

```python
def _reset(self) -> None:
    """Clear all caches and timestamps. For testing only."""
    _videos_cache.clear()
    _analyses_cache.clear()
    _cache_timestamps.clear()
```

### Step 2: Create `backend/test_storage_adapter.py`

```python
"""Tests for StorageAdapter — Supabase + in-memory cache unified layer."""
import pytest
import time
from storage_adapter import StorageAdapter, _videos_cache, _analyses_cache, _cache_timestamps


@pytest.fixture
def store():
    adapter = StorageAdapter()
    adapter._reset()
    yield adapter
    adapter._reset()


class TestInsertVideo:
    def test_insert_video_returns_record(self, store):
        result = store.insert_video("vid_1", "test.mp4", user_id="user_1")
        assert result["id"] == "vid_1"
        assert result["filename"] == "test.mp4"
        assert result["user_id"] == "user_1"
        assert result["status"] == "uploaded"

    def test_insert_video_custom_status(self, store):
        result = store.insert_video("vid_2", "test.mp4", status="processing")
        assert result["status"] == "processing"

    def test_insert_video_populates_cache(self, store):
        store.insert_video("vid_3", "test.mp4")
        assert "vid_3" in _videos_cache
        assert _videos_cache["vid_3"]["filename"] == "test.mp4"

    def test_insert_video_touches_timestamp(self, store):
        store.insert_video("vid_4", "test.mp4")
        assert "v:vid_4" in _cache_timestamps


class TestGetVideo:
    def test_get_video_from_cache(self, store):
        store.insert_video("vid_5", "test.mp4")
        result = store.get_video("vid_5")
        assert result is not None
        assert result["id"] == "vid_5"

    def test_get_video_not_found(self, store):
        result = store.get_video("nonexistent")
        assert result is None

    def test_get_video_none_after_delete(self, store):
        store.insert_video("vid_6", "test.mp4")
        store.delete_video("vid_6")
        assert store.get_video("vid_6") is None


class TestListVideos:
    def test_list_videos_empty(self, store):
        assert store.list_videos() == []

    def test_list_videos_returns_all(self, store):
        store.insert_video("v1", "a.mp4")
        store.insert_video("v2", "b.mp4")
        store.insert_video("v3", "c.mp4")
        assert len(store.list_videos()) == 3

    def test_list_videos_respects_limit(self, store):
        for i in range(10):
            store.insert_video(f"v{i}", f"file{i}.mp4")
        assert len(store.list_videos(limit=5)) == 5


class TestUpdateVideoStatus:
    def test_update_status(self, store):
        store.insert_video("vid_7", "test.mp4")
        store.update_video_status("vid_7", "completed")
        assert store.get_video("vid_7")["status"] == "completed"


class TestDeleteVideo:
    def test_delete_removes_from_cache(self, store):
        store.insert_video("vid_8", "test.mp4")
        store.delete_video("vid_8")
        assert "vid_8" not in _videos_cache

    def test_delete_removes_timestamp(self, store):
        store.insert_video("vid_9", "test.mp4")
        store.delete_video("vid_9")
        assert "v:vid_9" not in _cache_timestamps


class TestInsertAnalysis:
    def test_insert_analysis_returns_record(self, store):
        analysis = {"hook_score": 0.8, "viral_potential": 0.6}
        result = store.insert_analysis("vid_10", analysis, user_id="user_1")
        assert result["video_id"] == "vid_10"
        assert result["user_id"] == "user_1"

    def test_insert_analysis_populates_cache(self, store):
        store.insert_analysis("vid_11", {"hook_score": 0.7})
        assert "vid_11" in _analyses_cache
        assert _analyses_cache["vid_11"]["hook_score"] == 0.7


class TestGetAnalysis:
    def test_get_analysis_from_cache(self, store):
        store.insert_analysis("vid_12", {"hook_score": 0.9})
        result = store.get_analysis("vid_12")
        assert result is not None
        assert result["hook_score"] == 0.9

    def test_get_analysis_not_found(self, store):
        assert store.get_analysis("nonexistent") is None

    def test_get_analysis_normalizes_supabase_wrapping(self, store):
        """Supabase stores {"data": {...}}, cache stores flat. get_analysis returns flat."""
        store.insert_analysis("vid_13", {"hook_score": 0.5, "risk_score": 0.3})
        result = store.get_analysis("vid_13")
        assert "data" not in result
        assert result["hook_score"] == 0.5


class TestDeleteAnalysis:
    def test_delete_removes_from_cache(self, store):
        store.insert_analysis("vid_14", {"score": 1.0})
        store.delete_analysis("vid_14")
        assert "vid_14" not in _analyses_cache


class TestWarmup:
    def test_warmup_returns_zero_without_supabase(self, store):
        assert store.warmup(limit=5) == 0


class TestGetCachedVideoIds:
    def test_get_cached_video_ids(self, store):
        store.insert_video("vid_15", "test.mp4")
        assert "vid_15" in store.get_cached_video_ids()


class TestGetAnalyticsSnapshot:
    def test_snapshot_empty(self, store):
        s = store.get_analytics_snapshot()
        assert s["total_analyses"] == 0
        assert s["total_videos"] == 0

    def test_snapshot_with_data(self, store):
        store.insert_video("vid_16", "test.mp4")
        store.insert_analysis("vid_16", {"hook_score": 0.8, "viral_potential": 0.6})
        s = store.get_analytics_snapshot()
        assert s["total_videos"] >= 1
        assert s["total_analyses"] >= 1


class TestCacheEviction:
    def test_evict_removes_expired_videos(self, store):
        store.insert_video("vid_17", "test.mp4")
        _cache_timestamps["v:vid_17"] = time.time() - 7200
        store._evict_stale()
        assert "vid_17" not in _videos_cache

    def test_evict_keeps_fresh_videos(self, store):
        store.insert_video("vid_18", "test.mp4")
        store._evict_stale()
        assert "vid_18" in _videos_cache

    def test_evict_removes_expired_analyses(self, store):
        store.insert_analysis("vid_19", {"score": 1.0})
        _cache_timestamps["a:vid_19"] = time.time() - 3600
        store._evict_stale()
        assert "vid_19" not in _analyses_cache
```

### Step 3: Run tests
```bash
cd backend && python -m pytest test_storage_adapter.py -v
```
Expected: 22 PASS

### Step 4: Commit
```bash
git add backend/storage_adapter.py backend/test_storage_adapter.py
git commit -m "feat: add StorageAdapter tests (22 tests)"
```

---

## T2: JWT Auth Tests

### Step 1: Add test helper to main.py

Add near bottom of `backend/main.py`:

```python
def _set_jwt_secret_for_test(secret: str) -> None:
    """Override JWT secret for testing. NOT for production use."""
    global _JWT_SECRET
    _JWT_SECRET = secret
```

### Step 2: Create `backend/test_jwt_auth.py`

```python
"""Tests for JWT authentication functions in main.py."""
import pytest
from fastapi import HTTPException
import jwt
import time


def _make_token(sub="user_123", exp_offset=3600, secret="test-secret"):
    payload = {"sub": sub, "exp": time.time() + exp_offset, "aud": "authenticated"}
    return jwt.encode(payload, secret, algorithm="HS256")


class TestGetVerifiedUserId:
    """Permissive auth — never raises."""

    def test_valid_jwt_returns_sub(self):
        from main import get_verified_user_id, _set_jwt_secret_for_test
        _set_jwt_secret_for_test("test-secret")
        token = _make_token(sub="user_abc", secret="test-secret")
        assert get_verified_user_id(f"Bearer {token}", "guest") == "user_abc"

    def test_expired_falls_back(self):
        from main import get_verified_user_id, _set_jwt_secret_for_test
        _set_jwt_secret_for_test("test-secret")
        token = _make_token(sub="user_abc", exp_offset=-3600, secret="test-secret")
        assert get_verified_user_id(f"Bearer {token}", "guest_user") == "guest_user"

    def test_invalid_falls_back(self):
        from main import get_verified_user_id, _set_jwt_secret_for_test
        _set_jwt_secret_for_test("test-secret")
        token = _make_token(sub="user_abc", secret="wrong-secret")
        assert get_verified_user_id(f"Bearer {token}", "guest_user") == "guest_user"

    def test_no_jwt_returns_form_user_id(self):
        from main import get_verified_user_id, _set_jwt_secret_for_test
        _set_jwt_secret_for_test("test-secret")
        assert get_verified_user_id(None, "anonymous") == "anonymous"

    def test_no_secret_returns_form_user_id(self):
        from main import get_verified_user_id, _set_jwt_secret_for_test
        _set_jwt_secret_for_test("")
        token = _make_token(sub="user_abc", secret="anything")
        assert get_verified_user_id(f"Bearer {token}", "guest") == "guest"


class TestRequireAuthUser:
    """Strict auth — raises 401 on failure."""

    def test_valid_jwt_returns_sub(self):
        from main import require_auth_user, _set_jwt_secret_for_test
        _set_jwt_secret_for_test("test-secret")
        token = _make_token(sub="user_abc", secret="test-secret")
        assert require_auth_user(f"Bearer {token}") == "user_abc"

    def test_no_token_raises_401(self):
        from main import require_auth_user, _set_jwt_secret_for_test
        _set_jwt_secret_for_test("test-secret")
        with pytest.raises(HTTPException) as exc:
            require_auth_user(None)
        assert exc.value.status_code == 401

    def test_expired_raises_401(self):
        from main import require_auth_user, _set_jwt_secret_for_test
        _set_jwt_secret_for_test("test-secret")
        token = _make_token(sub="user_abc", exp_offset=-3600, secret="test-secret")
        with pytest.raises(HTTPException) as exc:
            require_auth_user(f"Bearer {token}")
        assert exc.value.status_code == 401

    def test_invalid_raises_401(self):
        from main import require_auth_user, _set_jwt_secret_for_test
        _set_jwt_secret_for_test("test-secret")
        token = _make_token(sub="user_abc", secret="wrong-secret")
        with pytest.raises(HTTPException) as exc:
            require_auth_user(f"Bearer {token}")
        assert exc.value.status_code == 401

    def test_no_secret_returns_anonymous(self):
        from main import require_auth_user, _set_jwt_secret_for_test
        _set_jwt_secret_for_test("")
        assert require_auth_user(None) == "anonymous"
```

### Step 3: Run tests
```bash
cd backend && python -m pytest test_jwt_auth.py -v
```
Expected: 10 PASS

### Step 4: Commit
```bash
git add backend/main.py backend/test_jwt_auth.py
git commit -m "feat: add JWT auth tests (10 tests)"
```

---

## T3: Stripe Webhook Tests

### Step 1: Verify webhook endpoint exists in main.py

Check `POST /api/stripe/webhook` handles:
- `checkout.session.completed` → `_premium_users.add(user_id)`
- `customer.subscription.deleted` → `_premium_users.discard(user_id)`
- `invoice.payment_failed` → logs

If missing, add the endpoint (see master plan for full code).

### Step 2: Create `backend/test_stripe_webhook.py`

```python
"""Tests for Stripe webhook handling."""
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient


class TestStripeWebhookConfigured:
    @patch("main.settings.stripe_webhook_secret", "whsec_test")
    @patch("main.settings.stripe_secret_key", "sk_test")
    def test_checkout_completed_activates_premium(self):
        from main import app, _premium_users
        _premium_users.clear()
        mock_event = {"type": "checkout.session.completed", "data": {"object": {"metadata": {"user_id": "premium_user_1"}}}}
        with patch("stripe.Webhook.construct_event", return_value=mock_event):
            client = TestClient(app)
            resp = client.post("/api/stripe/webhook", content=b'{}', headers={"stripe-signature": "test_sig"})
            assert resp.status_code == 200
            assert "premium_user_1" in _premium_users

    @patch("main.settings.stripe_webhook_secret", "whsec_test")
    @patch("main.settings.stripe_secret_key", "sk_test")
    def test_subscription_deleted_deactivates_premium(self):
        from main import app, _premium_users
        _premium_users.clear()
        _premium_users.add("churned_user")
        mock_event = {"type": "customer.subscription.deleted", "data": {"object": {"metadata": {"user_id": "churned_user"}}}}
        with patch("stripe.Webhook.construct_event", return_value=mock_event):
            client = TestClient(app)
            resp = client.post("/api/stripe/webhook", content=b'{}', headers={"stripe-signature": "test_sig"})
            assert resp.status_code == 200
            assert "churned_user" not in _premium_users

    @patch("main.settings.stripe_webhook_secret", "whsec_test")
    def test_invalid_signature_returns_400(self):
        from main import app
        with patch("stripe.Webhook.construct_event", side_effect=ValueError):
            client = TestClient(app)
            resp = client.post("/api/stripe/webhook", content=b"invalid", headers={"stripe-signature": "bad"})
            assert resp.status_code == 400


class TestStripeWebhookNotConfigured:
    @patch("main.settings.stripe_webhook_secret", "")
    def test_returns_501_when_not_configured(self):
        from main import app
        client = TestClient(app)
        assert client.post("/api/stripe/webhook").status_code == 501
```

### Step 3: Run tests
```bash
cd backend && python -m pytest test_stripe_webhook.py -v
```
Expected: 4 PASS

### Step 4: Commit
```bash
git add backend/main.py backend/test_stripe_webhook.py
git commit -m "feat: add Stripe webhook tests (4 tests)"
```

---

## T4: User-Friendly Error States

### Step 1: Add `_user_error()` helper to main.py

```python
def _user_error(message: str, detail: str = "", status_code: int = 500):
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=status_code, content={
        "error": message, "detail": detail,
        "help": "If this persists, try again in a few minutes or contact support.",
    })
```

### Step 2: Fix `_process_in_background` error handler

Ensure the except block does NOT re-raise:
```python
except Exception as e:
    _task_status[video_id] = {"status": "error", "progress": 0, "stage": "error",
        "message": "Analysis failed. Please try uploading again."}
    if os.path.exists(file_path):
        os.remove(file_path)
    _broadcast_progress(video_id, {"status": "error", "message": "Analysis failed. Please try again."})
    print(f"[ERROR] Processing failed for {video_id}: {e}")
    # Do NOT re-raise
```

### Step 3: Update dashboard error display

In `frontend/src/app/dashboard/page.tsx`, ensure error state has retry button.

### Step 4: Commit
```bash
git add backend/main.py frontend/src/app/dashboard/page.tsx
git commit -m "fix: add user-friendly error states with retry"
```

---

## T5: Email Digest Tests

### Step 1: Create `backend/test_email_digest.py`

```python
"""Tests for email digest functionality."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch


class TestDigestSubscribe:
    def test_subscribe_new_email(self):
        from main import app, _digest_subs
        _digest_subs.clear()
        client = TestClient(app)
        resp = client.post("/api/digest/subscribe", json={"email": "test@example.com", "frequency": "weekly"},
            headers={"authorization": "Bearer dummy"})
        assert resp.status_code == 200
        assert "test@example.com" in _digest_subs

    def test_subscribe_duplicate_returns_409(self):
        from main import app, _digest_subs
        _digest_subs.clear()
        _digest_subs["dup@example.com"] = {"frequency": "weekly"}
        client = TestClient(app)
        resp = client.post("/api/digest/subscribe", json={"email": "dup@example.com", "frequency": "weekly"},
            headers={"authorization": "Bearer dummy"})
        assert resp.status_code == 409


class TestDigestPreview:
    def test_preview_returns_stats(self):
        from main import app
        client = TestClient(app)
        resp = client.get("/api/digest/preview")
        assert resp.status_code == 200
        assert "total_analyses" in resp.json()


class TestSendEmailSmtp:
    @patch("main.settings.email_host", "smtp.example.com")
    @patch("main.settings.email_username", "user")
    @patch("main.settings.email_password", "pass")
    def test_smtp_not_reachable_returns_false(self):
        from main import _send_email_smtp
        assert _send_email_smtp("test@example.com", "Test", "<p>Test</p>") is False
```

### Step 2: Run tests
```bash
cd backend && python -m pytest test_email_digest.py -v
```
Expected: 4 PASS

### Step 3: Commit
```bash
git add backend/test_email_digest.py
git commit -m "feat: add email digest tests (4 tests)"
```

---

## T6: Full Test Suite Verification

### Step 1: Run all backend tests
```bash
cd backend && python -m pytest -v --tb=short
```
Expected: 93+ PASS

### Step 2: Run all frontend tests
```bash
cd frontend && npx vitest run
```
Expected: 16 PASS

### Step 3: Commit
```bash
git add . && git commit -m "v2.5: ship blockers complete"
```
