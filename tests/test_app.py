"""
Tests for Mergington High School Activities API
Using the AAA (Arrange-Act-Assert) pattern
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path to import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app

client = TestClient(app)


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_200(self):
        """Test that GET /activities returns status 200"""
        # Arrange
        expected_status = 200

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == expected_status

    def test_get_activities_returns_dict(self):
        """Test that GET /activities returns a dictionary"""
        # Arrange
        expected_type = dict

        # Act
        response = client.get("/activities")
        data = response.json()

        # Assert
        assert isinstance(data, expected_type)

    def test_get_activities_contains_expected_activities(self):
        """Test that activities list contains expected activities"""
        # Arrange
        expected_activities = [
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Soccer Team",
            "Basketball Club",
            "Art Club",
            "Drama Club",
            "Math Club",
            "Science Olympiad"
        ]

        # Act
        response = client.get("/activities")
        activities = response.json()

        # Assert
        for activity in expected_activities:
            assert activity in activities

    def test_activity_has_required_fields(self):
        """Test that each activity has required fields"""
        # Arrange
        required_fields = ["description", "schedule", "max_participants", "participants"]

        # Act
        response = client.get("/activities")
        activities = response.json()

        # Assert
        for activity_name, activity_data in activities.items():
            for field in required_fields:
                assert field in activity_data, f"Missing '{field}' in {activity_name}"
            assert isinstance(activity_data["participants"], list)


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self):
        """Test successful signup for an activity"""
        # Arrange
        activity_name = "Soccer Team"
        email = "newstudent@mergington.edu"
        expected_status = 200

        # Act
        response = client.post(
            f"/activities/{activity_name.replace(' ', '%20')}/signup?email={email}"
        )

        # Assert
        assert response.status_code == expected_status
        assert "Signed up" in response.json()["message"]

    def test_signup_duplicate_returns_400(self):
        """Test that duplicate signup returns 400 error"""
        # Arrange
        activity_name = "Basketball Club"
        email = "duplicate@mergington.edu"
        expected_status = 400
        first_signup_url = f"/activities/{activity_name.replace(' ', '%20')}/signup?email={email}"
        duplicate_signup_url = f"/activities/{activity_name.replace(' ', '%20')}/signup?email={email}"

        # Act
        client.post(first_signup_url)  # First signup succeeds
        response = client.post(duplicate_signup_url)  # Duplicate attempt

        # Assert
        assert response.status_code == expected_status
        assert "already signed up" in response.json()["detail"]

    def test_signup_nonexistent_activity_returns_404(self):
        """Test that signup for nonexistent activity returns 404"""
        # Arrange
        activity_name = "Nonexistent Club"
        email = "student@mergington.edu"
        expected_status = 404
        signup_url = f"/activities/{activity_name.replace(' ', '%20')}/signup?email={email}"

        # Act
        response = client.post(signup_url)

        # Assert
        assert response.status_code == expected_status
        assert "Activity not found" in response.json()["detail"]

    def test_signup_updates_participants_list(self):
        """Test that signup updates the participants list"""
        # Arrange
        activity_name = "Art Club"
        email = "tracked@mergington.edu"
        signup_url = f"/activities/{activity_name.replace(' ', '%20')}/signup?email={email}"

        # Act
        client.post(signup_url)
        response = client.get("/activities")
        activities = response.json()
        participants = activities[activity_name]["participants"]

        # Assert
        assert email in participants, f"{email} not found in {activity_name} participants"


class TestRemoveFromActivity:
    """Tests for DELETE /activities/{activity_name}/signup endpoint"""

    def test_remove_success(self):
        """Test successful removal from an activity"""
        # Arrange
        activity_name = "Drama Club"
        email = "remove-me@mergington.edu"
        expected_status = 200
        signup_url = f"/activities/{activity_name.replace(' ', '%20')}/signup?email={email}"
        remove_url = f"/activities/{activity_name.replace(' ', '%20')}/signup?email={email}"

        # Act
        client.post(signup_url)  # Sign up first
        response = client.delete(remove_url)  # Then remove

        # Assert
        assert response.status_code == expected_status
        assert "Removed" in response.json()["message"]

    def test_remove_nonexistent_enrollment_returns_400(self):
        """Test that removing non-existent enrollment returns 400"""
        # Arrange
        activity_name = "Math Club"
        email = "nothere@mergington.edu"
        expected_status = 400
        remove_url = f"/activities/{activity_name.replace(' ', '%20')}/signup?email={email}"

        # Act
        response = client.delete(remove_url)

        # Assert
        assert response.status_code == expected_status
        assert "not signed up" in response.json()["detail"]

    def test_remove_nonexistent_activity_returns_404(self):
        """Test that remove from nonexistent activity returns 404"""
        # Arrange
        activity_name = "Fake Club"
        email = "student@mergington.edu"
        expected_status = 404
        remove_url = f"/activities/{activity_name.replace(' ', '%20')}/signup?email={email}"

        # Act
        response = client.delete(remove_url)

        # Assert
        assert response.status_code == expected_status
        assert "Activity not found" in response.json()["detail"]

    def test_remove_updates_participants_list(self):
        """Test that removal updates the participants list"""
        # Arrange
        activity_name = "Science Olympiad"
        email = "bye@mergington.edu"
        signup_url = f"/activities/{activity_name.replace(' ', '%20')}/signup?email={email}"
        remove_url = f"/activities/{activity_name.replace(' ', '%20')}/signup?email={email}"

        # Act
        client.post(signup_url)  # Sign up
        client.delete(remove_url)  # Remove
        response = client.get("/activities")
        activities = response.json()
        participants = activities[activity_name]["participants"]

        # Assert
        assert email not in participants, f"{email} still in {activity_name} participants"


class TestRootRedirect:
    """Tests for GET / endpoint"""

    def test_root_redirect_to_html(self):
        """Test that root redirects to static HTML"""
        # Arrange
        expected_status = 307
        expected_location = "/static/index.html"

        # Act
        response = client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code == expected_status
        assert expected_location in response.headers["location"]


class TestActivityValidation:
    """Integration tests for activity validation"""

    def test_signup_respects_max_participants(self):
        """Test that signup doesn't exceed max participants (if implemented)"""
        # Arrange
        activity_name = "Chess Club"
        max_participants = 12

        # Act
        response = client.get("/activities")
        chess_club = response.json()["Chess Club"]
        current_participants = len(chess_club["participants"])

        # Assert
        assert current_participants <= max_participants

    def test_participants_list_integrity(self):
        """Test that participants list maintains integrity after operations"""
        # Arrange
        activity_name = "Programming Class"
        test_email = "integrity@mergington.edu"
        signup_url = f"/activities/{activity_name.replace(' ', '%20')}/signup?email={test_email}"
        remove_url = f"/activities/{activity_name.replace(' ', '%20')}/signup?email={test_email}"

        # Act
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()[activity_name]["participants"])

        client.post(signup_url)
        after_signup = client.get("/activities")
        signup_count = len(after_signup.json()[activity_name]["participants"])

        client.delete(remove_url)
        after_removal = client.get("/activities")
        final_count = len(after_removal.json()[activity_name]["participants"])

        # Assert
        assert signup_count == initial_count + 1, "Participant count didn't increase after signup"
        assert final_count == initial_count, "Participant count didn't return to original after removal"
