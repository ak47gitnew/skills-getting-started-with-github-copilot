"""
FastAPI tests for Mergington High School Activities API
Using AAA (Arrange-Act-Assert) pattern for clear test structure
"""

import pytest
from fastapi.testclient import TestClient


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_all_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all available activities"""
        # Arrange
        expected_activities = [
            "Chess Club", "Programming Class", "Gym Class", "Basketball Team",
            "Tennis Club", "Art Studio", "Music Performance", "Debate Club", "Science Club"
        ]

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        activities = response.json()
        assert len(activities) == 9
        for activity_name in expected_activities:
            assert activity_name in activities

    def test_get_activities_returns_correct_structure(self, client):
        """Test that activities have all required fields"""
        # Arrange
        required_fields = ["description", "schedule", "max_participants", "participants"]

        # Act
        response = client.get("/activities")
        activities = response.json()

        # Assert
        for activity_name, activity_data in activities.items():
            for field in required_fields:
                assert field in activity_data, f"Missing field '{field}' in {activity_name}"

    def test_get_activities_participants_are_lists(self, client):
        """Test that participants field is a list of emails"""
        # Arrange
        # Act
        response = client.get("/activities")
        activities = response.json()

        # Assert
        for activity_name, activity_data in activities.items():
            assert isinstance(activity_data["participants"], list), \
                f"Participants for {activity_name} is not a list"
            for participant in activity_data["participants"]:
                assert "@" in participant, f"Invalid email format: {participant}"


class TestRootRedirect:
    """Tests for GET / endpoint"""

    def test_root_redirects_to_static_index(self, client):
        """Test that root path redirects to static/index.html"""
        # Arrange
        # Act
        response = client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_valid_activity_new_email_succeeds(self, client):
        """Test successful signup with valid activity and new email"""
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
        assert email in response.json()["message"]

    def test_signup_increases_participant_count(self, client):
        """Test that signup adds participant to the activity"""
        # Arrange
        activity_name = "Art Studio"
        email = "newartist@mergington.edu"
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()[activity_name]["participants"])

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 200
        updated_response = client.get("/activities")
        updated_count = len(updated_response.json()[activity_name]["participants"])
        assert updated_count == initial_count + 1
        assert email in updated_response.json()[activity_name]["participants"]

    def test_signup_duplicate_email_returns_409_conflict(self, client):
        """Test that signing up with same email twice returns 409 Conflict"""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already signed up

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 409
        assert "already signed up" in response.json()["detail"]

    def test_signup_nonexistent_activity_returns_404(self, client):
        """Test that signing up for non-existent activity returns 404"""
        # Arrange
        activity_name = "Nonexistent Club"
        email = "student@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_signup_with_encoded_email(self, client):
        """Test signup with email containing special characters"""
        # Arrange
        activity_name = "Programming Class"
        email = "student+tag@mergington.edu"
        from urllib.parse import urlencode

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?{urlencode({'email': email})}"
        )

        # Assert
        assert response.status_code == 200
        updated_response = client.get("/activities")
        assert email in updated_response.json()[activity_name]["participants"]

    def test_signup_with_activity_name_with_spaces(self, client):
        """Test signup for activity with spaces in name"""
        # Arrange
        activity_name = "Programming Class"  # Has space
        email = "coder@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 200
        updated_response = client.get("/activities")
        assert email in updated_response.json()[activity_name]["participants"]


class TestUnregisterFromActivity:
    """Tests for POST /activities/{activity_name}/unregister endpoint"""

    def test_unregister_existing_participant_succeeds(self, client):
        """Test successful unregister of an existing participant"""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already signed up

        # Act
        response = client.post(
            f"/activities/{activity_name}/unregister?email={email}"
        )

        # Assert
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]
        assert email in response.json()["message"]

    def test_unregister_decreases_participant_count(self, client):
        """Test that unregister removes participant from the activity"""
        # Arrange
        activity_name = "Music Performance"
        email = "noah@mergington.edu"  # Already signed up
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()[activity_name]["participants"])

        # Act
        response = client.post(
            f"/activities/{activity_name}/unregister?email={email}"
        )

        # Assert
        assert response.status_code == 200
        updated_response = client.get("/activities")
        updated_count = len(updated_response.json()[activity_name]["participants"])
        assert updated_count == initial_count - 1
        assert email not in updated_response.json()[activity_name]["participants"]

    def test_unregister_nonexistent_participant_returns_404(self, client):
        """Test that unregistering non-existent participant returns 404"""
        # Arrange
        activity_name = "Tennis Club"
        email = "ghoststudent@mergington.edu"  # Not signed up

        # Act
        response = client.post(
            f"/activities/{activity_name}/unregister?email={email}"
        )

        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_unregister_from_nonexistent_activity_returns_404(self, client):
        """Test that unregistering from non-existent activity returns 404"""
        # Arrange
        activity_name = "Fake Club"
        email = "student@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/unregister?email={email}"
        )

        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_unregister_actually_removes_from_list(self, client):
        """Test that participant is actually removed from participants list"""
        # Arrange
        activity_name = "Debate Club"
        email = "jackson@mergington.edu"
        initial_response = client.get("/activities")
        assert email in initial_response.json()[activity_name]["participants"]

        # Act
        response = client.post(
            f"/activities/{activity_name}/unregister?email={email}"
        )

        # Assert
        assert response.status_code == 200
        updated_response = client.get("/activities")
        participants = updated_response.json()[activity_name]["participants"]
        assert email not in participants
        # Verify by attempting to unregister again (should fail)
        second_response = client.post(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        assert second_response.status_code == 404
