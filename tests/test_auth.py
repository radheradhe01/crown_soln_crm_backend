import pytest
from app.core.config import settings

@pytest.mark.asyncio
async def test_login_access_token(client):
    login_data = {
        "username": "admin@crm.com",
        "password": "admin123456"
    }
    response = await client.post(f"{settings.API_V1_STR}/auth/login", data=login_data)
    assert response.status_code == 200
    tokens = response.json()
    assert "access_token" in tokens
    assert tokens["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_read_users_me(client):
    # First login to get token
    login_data = {
        "username": "admin@crm.com",
        "password": "admin123456"
    }
    login_response = await client.post(f"{settings.API_V1_STR}/auth/login", data=login_data)
    token = login_response.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.get(f"{settings.API_V1_STR}/auth/me", headers=headers)
    assert response.status_code == 200
    user = response.json()
    assert user["email"] == "admin@crm.com"
    assert user["role"] == "ADMIN"
