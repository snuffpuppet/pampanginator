"""
Tests for /api/feedback endpoints.

All database calls are mocked via services.feedback.
"""

from unittest.mock import AsyncMock, patch


async def test_submit_thumbs_up(client):
    with patch("services.feedback.write_feedback", new=AsyncMock(return_value="fb-001")):
        response = await client.post("/api/feedback", json={
            "interaction_id": "iid-1",
            "rating": "thumbs_up",
        })
    assert response.status_code == 201
    assert response.json() == {"id": "fb-001", "status": "recorded"}


async def test_submit_thumbs_down_with_correction(client):
    with patch("services.feedback.write_feedback", new=AsyncMock(return_value="fb-002")):
        response = await client.post("/api/feedback", json={
            "interaction_id": "iid-2",
            "rating": "thumbs_down",
            "correction_kapampangan": "Mangan ku.",
            "correction_english": "I will eat.",
            "correction_note": "Model used wrong form",
            "corrected_by": "native_speaker",
            "authority_level": 1,
        })
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "fb-002"


async def test_submit_invalid_rating_returns_422(client):
    response = await client.post("/api/feedback", json={
        "interaction_id": "iid-3",
        "rating": "shrug",
    })
    assert response.status_code == 422


async def test_submit_missing_rating_returns_422(client):
    response = await client.post("/api/feedback", json={"interaction_id": "iid-4"})
    assert response.status_code == 422


async def test_submit_feedback_service_error_returns_500(client):
    with patch("services.feedback.write_feedback", new=AsyncMock(side_effect=Exception("DB error"))):
        response = await client.post("/api/feedback", json={
            "rating": "thumbs_up",
        })
    assert response.status_code == 500


async def test_get_pending_feedback(client):
    records = [{"id": "fb-1", "rating": "thumbs_down", "reviewed": False}]
    with patch("services.feedback.get_pending", new=AsyncMock(return_value=records)):
        response = await client.get("/api/feedback/pending")
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["records"] == records


async def test_get_pending_feedback_empty(client):
    with patch("services.feedback.get_pending", new=AsyncMock(return_value=[])):
        response = await client.get("/api/feedback/pending")
    assert response.status_code == 200
    assert response.json() == {"count": 0, "records": []}


async def test_get_pending_feedback_service_error_returns_500(client):
    with patch("services.feedback.get_pending", new=AsyncMock(side_effect=Exception("DB error"))):
        response = await client.get("/api/feedback/pending")
    assert response.status_code == 500


async def test_get_all_feedback(client):
    records = [{"id": "fb-1"}, {"id": "fb-2"}]
    with patch("services.feedback.get_all", new=AsyncMock(return_value=records)):
        response = await client.get("/api/feedback")
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 2


async def test_get_all_feedback_passes_filters(client):
    with patch("services.feedback.get_all", new=AsyncMock(return_value=[])) as mock_get:
        await client.get("/api/feedback?rating=thumbs_up&authority_level=1&applied=true")
    mock_get.assert_called_once_with(
        rating="thumbs_up",
        authority_level=1,
        applied=True,
        after=None,
        before=None,
    )


async def test_get_all_feedback_date_filters(client):
    with patch("services.feedback.get_all", new=AsyncMock(return_value=[])) as mock_get:
        await client.get("/api/feedback?after=2024-01-01&before=2024-12-31")
    mock_get.assert_called_once_with(
        rating=None,
        authority_level=None,
        applied=None,
        after="2024-01-01",
        before="2024-12-31",
    )


async def test_approve_feedback(client):
    result = {"status": "approved", "id": "fb-1", "vocab_written": False}
    with patch("services.feedback.approve", new=AsyncMock(return_value=result)):
        response = await client.post("/api/feedback/fb-1/approve", json={})
    assert response.status_code == 200
    assert response.json()["status"] == "approved"


async def test_approve_feedback_with_authority_override(client):
    result = {"status": "approved", "id": "fb-1"}
    with patch("services.feedback.approve", new=AsyncMock(return_value=result)) as mock_approve:
        await client.post("/api/feedback/fb-1/approve", json={"authority_level": 2})
    mock_approve.assert_called_once_with("fb-1", authority_level=2)


async def test_approve_feedback_not_found(client):
    with patch("services.feedback.approve", new=AsyncMock(side_effect=ValueError("not found"))):
        response = await client.post("/api/feedback/missing/approve", json={})
    assert response.status_code == 404


async def test_approve_feedback_service_error_returns_500(client):
    with patch("services.feedback.approve", new=AsyncMock(side_effect=Exception("DB error"))):
        response = await client.post("/api/feedback/fb-1/approve", json={})
    assert response.status_code == 500


async def test_reject_feedback(client):
    result = {"status": "rejected", "id": "fb-1"}
    with patch("services.feedback.reject", new=AsyncMock(return_value=result)):
        response = await client.post("/api/feedback/fb-1/reject")
    assert response.status_code == 200
    assert response.json()["status"] == "rejected"


async def test_reject_feedback_not_found(client):
    with patch("services.feedback.reject", new=AsyncMock(side_effect=ValueError("not found"))):
        response = await client.post("/api/feedback/missing/reject")
    assert response.status_code == 404
