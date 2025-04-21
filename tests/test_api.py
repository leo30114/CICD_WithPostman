import pytest
import httpx
from httpx import ASGITransport
from main import app  

# ── 1.1.1 pytest-asyncio ──
@pytest.fixture
def anyio_backend():
    return "asyncio"

# ── 1.1.2 pytest-asyncio ──
@pytest.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport = transport, base_url="http://testserver") as client:
        yield client

# ── 1.2.1 pytest-asyncio ──
@pytest.mark.anyio
async def test_create_item(async_client):
    payload = {"name": "pytest-foo", "description": "via HTTPX"}
    resp = await async_client.post("/items/", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    # Check if the response contains the expected keys
    assert data["name"] == payload["name"]
    assert "id" in data

# ── 1.2.2 pytest-asyncio ──
@pytest.mark.anyio
async def test_read_items(async_client):
    resp = await async_client.get("/items/")
    assert resp.status_code == 200
    items = resp.json()
    assert isinstance(items, list)


@pytest.mark.anyio
async def test_update_and_delete_item(async_client):
    # Create an item to update and delete
    resp = await async_client.post("/items/", json={"name":"updel","description":"x"})
    item = resp.json()
    item_id = item["id"]


    new_payload = {"name": "updated", "description": "changed"}
    resp2 = await async_client.put(f"/items/{item_id}", json=new_payload)
    assert resp2.status_code == 200
    assert resp2.json()["name"] == "updated"


    resp3 = await async_client.delete(f"/items/{item_id}")
    assert resp3.status_code == 200
    assert resp3.json() == {"ok": True}