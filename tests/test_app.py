from fastapi.testclient import TestClient

from src.app import app

client = TestClient(app)


def test_unregister_participant_removes_email_from_activity():
    response = client.delete(
        "/activities/Chess Club/unregister?email=michael@mergington.edu"
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Unregistered michael@mergington.edu from Chess Club"

    activities = client.get("/activities").json()
    assert "michael@mergington.edu" not in activities["Chess Club"]["participants"]


def test_unregister_participant_returns_404_for_unknown_activity():
    response = client.delete("/activities/Unknown Club/unregister?email=test@example.com")

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_participant_returns_400_if_not_enrolled():
    response = client.delete("/activities/Chess Club/unregister?email=not-enrolled@example.com")

    assert response.status_code == 400
    assert response.json()["detail"] == "Student is not registered for this activity"
