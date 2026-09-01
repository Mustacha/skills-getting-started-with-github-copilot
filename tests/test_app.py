"""
Test suite for Mergington High School Activities Management API

Covers all endpoints with happy-path and error-case scenarios:
- GET /activities: Retrieve all activities with participant lists
- POST /activities/{activity_name}/signup: Register a student for an activity
- DELETE /activities/{activity_name}/unregister: Remove a student from an activity
"""

from fastapi.testclient import TestClient

from src.app import app

client = TestClient(app)

# =============================================================================
# GET /activities Tests
# =============================================================================


def test_get_activities_returns_all_activities():
    """Happy path: Verify all 9 activities are returned with correct structure"""
    response = client.get("/activities")
    
    assert response.status_code == 200
    activities = response.json()
    
    # Verify all 9 activities are present
    expected_activities = [
        "Chess Club", "Programming Class", "Gym Class", "Basketball Team",
        "Tennis Club", "Drama Club", "Art Studio", "Debate Team", "Science Club"
    ]
    assert list(activities.keys()) == expected_activities
    
    # Verify each activity has required fields
    for activity_name, activity_details in activities.items():
        assert "description" in activity_details
        assert "schedule" in activity_details
        assert "max_participants" in activity_details
        assert "participants" in activity_details
        assert isinstance(activity_details["participants"], list)


def test_get_activities_participant_counts_match():
    """Verify participant lists contain correct initial participants"""
    response = client.get("/activities")
    activities = response.json()
    
    # Check a few activities have expected initial participants
    assert "michael@mergington.edu" in activities["Chess Club"]["participants"]
    assert "daniel@mergington.edu" in activities["Chess Club"]["participants"]
    assert "emma@mergington.edu" in activities["Programming Class"]["participants"]


# =============================================================================
# POST /activities/{activity_name}/signup Tests
# =============================================================================


def test_signup_new_participant_for_activity():
    """Happy path: Student can successfully sign up for an activity"""
    email = "newstudent@example.com"
    activity_name = "Chess Club"
    
    response = client.post(
        f"/activities/{activity_name}/signup?email={email}"
    )
    
    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for {activity_name}"
    
    # Verify participant was added
    activities = client.get("/activities").json()
    assert email in activities[activity_name]["participants"]


def test_signup_multiple_participants_for_same_activity():
    """Verify multiple students can sign up for the same activity"""
    email1 = "student1@example.com"
    email2 = "student2@example.com"
    activity_name = "Gym Class"
    
    response1 = client.post(
        f"/activities/{activity_name}/signup?email={email1}"
    )
    response2 = client.post(
        f"/activities/{activity_name}/signup?email={email2}"
    )
    
    assert response1.status_code == 200
    assert response2.status_code == 200
    
    activities = client.get("/activities").json()
    assert email1 in activities[activity_name]["participants"]
    assert email2 in activities[activity_name]["participants"]


def test_signup_returns_404_for_unknown_activity():
    """Error case: Return 404 if activity doesn't exist"""
    response = client.post(
        "/activities/Nonexistent Club/signup?email=test@example.com"
    )
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_returns_400_if_already_enrolled():
    """Error case: Return 400 if student is already signed up"""
    email = "michael@mergington.edu"  # Already enrolled in Chess Club
    
    response = client.post(
        f"/activities/Chess Club/signup?email={email}"
    )
    
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_multiple_activities():
    """Verify a student can sign up for multiple different activities"""
    email = "versatile@example.com"
    
    response1 = client.post(
        f"/activities/Art Studio/signup?email={email}"
    )
    response2 = client.post(
        f"/activities/Debate Team/signup?email={email}"
    )
    
    assert response1.status_code == 200
    assert response2.status_code == 200
    
    activities = client.get("/activities").json()
    assert email in activities["Art Studio"]["participants"]
    assert email in activities["Debate Team"]["participants"]


# =============================================================================
# DELETE /activities/{activity_name}/unregister Tests
# =============================================================================


def test_unregister_participant_removes_email_from_activity():
    """Happy path: Student can successfully unregister from an activity"""
    response = client.delete(
        "/activities/Chess Club/unregister?email=michael@mergington.edu"
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Unregistered michael@mergington.edu from Chess Club"

    activities = client.get("/activities").json()
    assert "michael@mergington.edu" not in activities["Chess Club"]["participants"]


def test_unregister_participant_returns_404_for_unknown_activity():
    """Error case: Return 404 if activity doesn't exist"""
    response = client.delete("/activities/Unknown Club/unregister?email=test@example.com")

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_participant_returns_400_if_not_enrolled():
    """Error case: Return 400 if student is not registered for the activity"""
    response = client.delete("/activities/Chess Club/unregister?email=not-enrolled@example.com")

    assert response.status_code == 400
    assert response.json()["detail"] == "Student is not registered for this activity"


def test_unregister_then_signup_again():
    """Edge case: Student can re-sign up after unregistering"""
    email = "cycling@example.com"
    activity_name = "Basketball Team"
    
    # Sign up
    signup_response = client.post(
        f"/activities/{activity_name}/signup?email={email}"
    )
    assert signup_response.status_code == 200
    
    # Unregister
    unregister_response = client.delete(
        f"/activities/{activity_name}/unregister?email={email}"
    )
    assert unregister_response.status_code == 200
    
    # Sign up again
    signup_again_response = client.post(
        f"/activities/{activity_name}/signup?email={email}"
    )
    assert signup_again_response.status_code == 200
    
    # Verify participant is in the list
    activities = client.get("/activities").json()
    assert email in activities[activity_name]["participants"]


def test_unregister_multiple_participants():
    """Verify unregistering one participant doesn't affect others"""
    email1 = "participant1@example.com"
    email2 = "participant2@example.com"
    activity_name = "Tennis Club"
    
    # Both sign up
    client.post(f"/activities/{activity_name}/signup?email={email1}")
    client.post(f"/activities/{activity_name}/signup?email={email2}")
    
    # Unregister first participant
    response = client.delete(
        f"/activities/{activity_name}/unregister?email={email1}"
    )
    assert response.status_code == 200
    
    # Verify only first was removed
    activities = client.get("/activities").json()
    assert email1 not in activities[activity_name]["participants"]
    assert email2 in activities[activity_name]["participants"]
