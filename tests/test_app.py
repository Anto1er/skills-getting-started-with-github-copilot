"""
Tests for the FastAPI application endpoints.
"""

import pytest


def test_root_redirect(client):
    """Test that root redirects to static index.html"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities(client):
    """Test getting all activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    
    data = response.json()
    assert "Chess Club" in data
    assert "Programming Class" in data
    assert len(data) == 9
    
    # Verify activity structure
    chess = data["Chess Club"]
    assert chess["description"] == "Learn strategies and compete in chess tournaments"
    assert chess["schedule"] == "Fridays, 3:30 PM - 5:00 PM"
    assert chess["max_participants"] == 12
    assert "michael@mergington.edu" in chess["participants"]


def test_signup_success(client):
    """Test successful signup for an activity"""
    response = client.post(
        "/activities/Chess Club/signup?email=newstudent@mergington.edu"
    )
    assert response.status_code == 200
    
    data = response.json()
    assert "Signed up newstudent@mergington.edu for Chess Club" in data["message"]
    
    # Verify participant was added
    activities_response = client.get("/activities")
    activities = activities_response.json()
    assert "newstudent@mergington.edu" in activities["Chess Club"]["participants"]


def test_signup_duplicate(client):
    """Test signing up when already registered"""
    # First signup
    client.post("/activities/Chess Club/signup?email=test@mergington.edu")
    
    # Try to signup again
    response = client.post(
        "/activities/Chess Club/signup?email=test@mergington.edu"
    )
    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"]


def test_signup_invalid_activity(client):
    """Test signing up for non-existent activity"""
    response = client.post(
        "/activities/Nonexistent Club/signup?email=test@mergington.edu"
    )
    assert response.status_code == 404
    assert "Activity not found" in response.json()["detail"]


def test_remove_participant_success(client):
    """Test successfully removing a participant"""
    response = client.delete(
        "/activities/Chess Club/participants/michael@mergington.edu"
    )
    assert response.status_code == 200
    
    data = response.json()
    assert "Removed michael@mergington.edu from Chess Club" in data["message"]
    
    # Verify participant was removed
    activities_response = client.get("/activities")
    activities = activities_response.json()
    assert "michael@mergington.edu" not in activities["Chess Club"]["participants"]


def test_remove_participant_not_found(client):
    """Test removing a participant who is not signed up"""
    response = client.delete(
        "/activities/Chess Club/participants/nonexistent@mergington.edu"
    )
    assert response.status_code == 404
    assert "Participant not found" in response.json()["detail"]


def test_remove_participant_invalid_activity(client):
    """Test removing participant from non-existent activity"""
    response = client.delete(
        "/activities/Nonexistent Club/participants/test@mergington.edu"
    )
    assert response.status_code == 404
    assert "Activity not found" in response.json()["detail"]


def test_full_signup_and_removal_workflow(client):
    """Test complete workflow of signing up and removing a participant"""
    email = "workflow@mergington.edu"
    activity = "Programming Class"
    
    # Get initial participant count
    initial_response = client.get("/activities")
    initial_count = len(initial_response.json()[activity]["participants"])
    
    # Sign up
    signup_response = client.post(
        f"/activities/{activity}/signup?email={email}"
    )
    assert signup_response.status_code == 200
    
    # Verify participant added
    after_signup = client.get("/activities")
    assert len(after_signup.json()[activity]["participants"]) == initial_count + 1
    assert email in after_signup.json()[activity]["participants"]
    
    # Remove participant
    remove_response = client.delete(
        f"/activities/{activity}/participants/{email}"
    )
    assert remove_response.status_code == 200
    
    # Verify participant removed
    after_removal = client.get("/activities")
    assert len(after_removal.json()[activity]["participants"]) == initial_count
    assert email not in after_removal.json()[activity]["participants"]


def test_activity_has_correct_participant_count(client):
    """Test that each activity has the expected initial participants"""
    response = client.get("/activities")
    activities = response.json()
    
    # Each activity should start with exactly 2 participants
    for activity_name, details in activities.items():
        assert len(details["participants"]) == 2, \
            f"{activity_name} should have 2 participants"
