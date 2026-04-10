async def test_health_returns_ok(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_health_is_fast(client):
    """Health probe must not require DB or LLM — it should always respond."""
    import time
    t0 = time.monotonic()
    response = await client.get("/health")
    elapsed = time.monotonic() - t0
    assert response.status_code == 200
    assert elapsed < 1.0
