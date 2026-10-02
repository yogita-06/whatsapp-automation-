import pytest

async def send(client, phone, message): return await client.post("/demo/message", json={"phone":phone,"message":message})

@pytest.mark.asyncio
async def test_complete_appointment_flow(client):
    phone = "+919999999999"
    r = await send(client, phone, "Hi"); assert "Welcome" in r.json()["reply"] and r.json()["state"] == "MAIN_MENU"
    assert (await send(client, phone, "1")).json()["state"] == "WAITING_FOR_NAME"
    assert (await send(client, phone, "Yogita")).json()["state"] == "WAITING_FOR_TREATMENT"
    assert (await send(client, phone, "2")).json()["state"] == "WAITING_FOR_DATE"
    assert (await send(client, phone, "Tomorrow")).json()["state"] == "WAITING_FOR_TIME"
    assert (await send(client, phone, "3")).json()["state"] == "REVIEW_APPOINTMENT"
    r = await send(client, phone, "1"); assert r.json()["state"] == "COMPLETED" and "request has been received" in r.json()["reply"]
    rows = (await client.get("/admin/appointments", headers={"X-API-Key":"test-key"})).json()
    assert len(rows) == 1 and rows[0]["name"] == "Yogita" and rows[0]["treatment"] == "Teeth Whitening" and rows[0]["status"] == "requested"

@pytest.mark.asyncio
async def test_global_commands_and_handoff(client):
    p = "+919111111111"; await send(client,p,"hi"); await send(client,p,"1")
    assert (await send(client,p,"MENU")).json()["state"] == "MAIN_MENU"
    await send(client,p,"1"); assert (await send(client,p,"RESET")).json()["state"] == "MAIN_MENU"
    assert (await send(client,p,"4")).json()["state"] == "WAITING_FOR_HUMAN"
    assert (await client.post(f"/admin/conversations/{p}/resume",headers={"X-API-Key":"test-key"})).status_code == 200

