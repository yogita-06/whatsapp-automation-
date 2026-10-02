import json
import pytest

@pytest.mark.asyncio
async def test_verification(client):
    ok = await client.get("/webhook", params={"hub.mode":"subscribe","hub.verify_token":"verify-me","hub.challenge":"123"})
    assert ok.status_code == 200 and ok.text == "123"
    assert (await client.get("/webhook", params={"hub.mode":"subscribe","hub.verify_token":"bad","hub.challenge":"123"})).status_code == 403

@pytest.mark.asyncio
async def test_duplicate_webhook(client):
    payload = json.load(open("tests/fixtures/incoming_text.json", encoding="utf-8"))
    assert (await client.post("/webhook", json=payload)).status_code == 200
    assert (await client.post("/webhook", json=payload)).status_code == 200
    rows = await client.get("/admin/messages", headers={"X-API-Key":"test-key"})
    incoming = [x for x in rows.json() if x["direction"] == "incoming"]
    assert len(incoming) == 1

