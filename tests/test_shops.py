import pytest

def test_create_wb_shop_success(client, authenticated_user, mock_supabase):
    payload = {
        "name": "My WB Shop",
        "marketplace": "wb",
        "wb_token": "test-wb-token",
        "fulfillment_models": ["FBS"]
    }
    response = client.post("/api/shops/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "My WB Shop"
    assert data["marketplace"] == "wb"
    assert data["wb_token"] == "test-wb-token"

def test_create_ozon_shop_success(client, authenticated_user, mock_supabase):
    payload = {
        "name": "My Ozon Shop",
        "marketplace": "ozon",
        "ozon_client_id": "client-id",
        "ozon_client_secret": "client-secret"
    }
    response = client.post("/api/shops/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["ozon_client_id"] == "client-id"

def test_create_ym_shop_success(client, authenticated_user, mock_supabase):
    payload = {
        "name": "My YM Shop",
        "marketplace": "ym",
        "ym_client_id": "client-id",
        "ym_campaign_id": "campaign-id"
    }
    response = client.post("/api/shops/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["ym_client_id"] == "client-id"

def test_create_shop_invalid_marketplace(client, authenticated_user):
    payload = {
        "name": "Bad Shop",
        "marketplace": "amazon",
    }
    response = client.post("/api/shops/", json=payload)
    assert response.status_code == 400

def test_admin_create_shop(client, authenticated_admin, mock_supabase):
    user_id = "3c3f9119-952d-42ec-99e2-9653765e9334"
    payload = {
        "name": "Admin WB Shop",
        "marketplace": "wb",
        "wb_token": "admin-test-token"
    }
    response = client.post(f"/api/admin/user/{user_id}/shops", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["user_id"] == user_id
    assert data["wb_token"] == "admin-test-token"
