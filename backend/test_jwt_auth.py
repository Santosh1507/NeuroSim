"""Tests for JWT authentication functions in main.py."""
import pytest
import pytest_asyncio
from fastapi import HTTPException
import jwt
import time


def _make_token(sub="user_123", exp_offset=3600, secret="test-secret"):
    """Helper to create valid JWT tokens for testing."""
    payload = {"sub": sub, "exp": time.time() + exp_offset, "aud": "authenticated"}
    return jwt.encode(payload, secret, algorithm="HS256")


class TestGetVerifiedUserId:
    """Permissive auth — never raises."""

    @pytest.mark.asyncio
    async def test_valid_jwt_returns_sub(self):
        from main import get_verified_user_id, _set_jwt_secret_for_test
        _set_jwt_secret_for_test("test-secret")
        token = _make_token(sub="user_abc", secret="test-secret")
        result = await get_verified_user_id(f"Bearer {token}", "guest")
        assert result == "user_abc"

    @pytest.mark.asyncio
    async def test_expired_falls_back(self):
        from main import get_verified_user_id, _set_jwt_secret_for_test
        _set_jwt_secret_for_test("test-secret")
        token = _make_token(sub="user_abc", exp_offset=-3600, secret="test-secret")
        result = await get_verified_user_id(f"Bearer {token}", "guest_user")
        assert result == "guest_user"

    @pytest.mark.asyncio
    async def test_invalid_falls_back(self):
        from main import get_verified_user_id, _set_jwt_secret_for_test
        _set_jwt_secret_for_test("test-secret")
        token = _make_token(sub="user_abc", secret="wrong-secret")
        result = await get_verified_user_id(f"Bearer {token}", "guest_user")
        assert result == "guest_user"

    @pytest.mark.asyncio
    async def test_no_jwt_returns_form_user_id(self):
        from main import get_verified_user_id, _set_jwt_secret_for_test
        _set_jwt_secret_for_test("test-secret")
        result = await get_verified_user_id(None, "anonymous")
        assert result == "anonymous"

    @pytest.mark.asyncio
    async def test_no_secret_returns_form_user_id(self):
        from main import get_verified_user_id, _set_jwt_secret_for_test
        _set_jwt_secret_for_test("")
        token = _make_token(sub="user_abc", secret="anything")
        result = await get_verified_user_id(f"Bearer {token}", "guest")
        assert result == "guest"


class TestRequireAuthUser:
    """Strict auth — raises 401 on failure."""

    @pytest.mark.asyncio
    async def test_valid_jwt_returns_sub(self):
        from main import require_auth_user, _set_jwt_secret_for_test
        _set_jwt_secret_for_test("test-secret")
        token = _make_token(sub="user_abc", secret="test-secret")
        result = await require_auth_user(f"Bearer {token}")
        assert result == "user_abc"

    @pytest.mark.asyncio
    async def test_no_token_raises_401(self):
        from main import require_auth_user, _set_jwt_secret_for_test
        _set_jwt_secret_for_test("test-secret")
        with pytest.raises(HTTPException) as exc:
            await require_auth_user(None)
        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_expired_raises_401(self):
        from main import require_auth_user, _set_jwt_secret_for_test
        _set_jwt_secret_for_test("test-secret")
        token = _make_token(sub="user_abc", exp_offset=-3600, secret="test-secret")
        with pytest.raises(HTTPException) as exc:
            await require_auth_user(f"Bearer {token}")
        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_raises_401(self):
        from main import require_auth_user, _set_jwt_secret_for_test
        _set_jwt_secret_for_test("test-secret")
        token = _make_token(sub="user_abc", secret="wrong-secret")
        with pytest.raises(HTTPException) as exc:
            await require_auth_user(f"Bearer {token}")
        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_no_secret_returns_anonymous(self):
        from main import require_auth_user, _set_jwt_secret_for_test
        _set_jwt_secret_for_test("")
        result = await require_auth_user(None)
        assert result == "anonymous"
