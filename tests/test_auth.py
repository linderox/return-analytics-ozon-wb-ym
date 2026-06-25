import pytest
from unittest.mock import patch, MagicMock

def test_get_profile_unauthorized(client):
    response = client.get("/api/profile/")
    # Since get_current_user raises 401 if no header
    assert response.status_code == 401

def test_yandex_auth_redirect(client):
    response = client.get("/api/auth/yandex", follow_redirects=False)
    assert response.status_code in (302, 307)
    assert "oauth.yandex.ru" in response.headers["location"]

def test_google_login_flow_mock(client):
    """Test placeholder for Google login verification."""
    # Since Google login is handled by Supabase directly on the frontend,
    # we verify the backend's JWKS auth which would process the Google-issued JWT.
    # This is indirectly covered by authenticated_user fixture.
    pass

@pytest.mark.integration
def test_login_linderox_success(client):
    """Verify login with email linderox@gmail.com : 12345678Aa"""
    import httpx
    import os
    # This requires a real Supabase endpoint
    supabase_url = os.getenv("SUPABASE_URL")
    url = f"{supabase_url}/auth/v1/token?grant_type=password"

    payload = {
        "email": "linderox@gmail.com",
        "password": "12345678Aa"
    }
    headers = {
        "apikey": os.getenv("SUPABASE_ANON_KEY"),
        "Content-Type": "application/json"
    }

    with httpx.Client() as http:
        resp = http.post(url, json=payload, headers=headers)
        # If credentials are correct, this should be 200
        assert resp.status_code == 200
        assert "access_token" in resp.json()

def test_admin_create_user(client, authenticated_admin, mock_supabase):
    payload = {
        "email": "newuser@example.com",
        "password": "Password123!",
        "fio": "New User",
        "plan": "basic"
    }

    # Mocking the external Supabase Auth call
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_resp.json.return_value = {"id": "new-uuid"}
        mock_post.return_value = mock_resp

        response = client.post("/api/admin/users/create", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["id"] == "new-uuid"
