"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app

# Create a test client
client = TestClient(app)


class TestGetActivities:
    """Test the GET /activities endpoint"""

    def test_get_activities_returns_200(self):
        """Test that /activities returns a 200 status code"""
        response = client.get("/activities")
        assert response.status_code == 200

    def test_get_activities_returns_dict(self):
        """Test that /activities returns a dictionary of activities"""
        response = client.get("/activities")
        activities = response.json()
        assert isinstance(activities, dict)
        assert len(activities) > 0

    def test_get_activities_has_required_fields(self):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_details in activities.items():
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)

    def test_get_activities_contains_expected_activities(self):
        """Test that expected activities are present"""
        response = client.get("/activities")
        activities = response.json()
        
        expected_activities = ["Basketball", "Tennis Club", "Drama Club"]
        for activity in expected_activities:
            assert activity in activities


class TestSignupForActivity:
    """Test the POST /activities/{activity_name}/signup endpoint"""

    def test_signup_valid_activity_and_email(self):
        """Test signing up with valid activity and email"""
        response = client.post(
            "/activities/Basketball/signup?email=test@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "test@mergington.edu" in data["message"]

    def test_signup_invalid_activity_returns_404(self):
        """Test that signing up for non-existent activity returns 404"""
        response = client.post(
            "/activities/NonExistentActivity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_duplicate_email_returns_400(self):
        """Test that signing up with duplicate email returns 400"""
        email = "duplicate@mergington.edu"
        
        # First signup - should succeed
        response1 = client.post(
            f"/activities/Basketball/signup?email={email}"
        )
        assert response1.status_code == 200
        
        # Second signup with same email - should fail
        response2 = client.post(
            f"/activities/Basketball/signup?email={email}"
        )
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]

    def test_signup_adds_participant_to_list(self):
        """Test that signup actually adds the participant to the activity"""
        email = "newstudent@mergington.edu"
        
        # Get initial participants count
        response_before = client.get("/activities")
        initial_count = len(response_before.json()["Tennis Club"]["participants"])
        
        # Sign up
        signup_response = client.post(
            f"/activities/Tennis Club/signup?email={email}"
        )
        assert signup_response.status_code == 200
        
        # Check participants count increased
        response_after = client.get("/activities")
        final_count = len(response_after.json()["Tennis Club"]["participants"])
        assert final_count == initial_count + 1
        assert email in response_after.json()["Tennis Club"]["participants"]


class TestUnregisterFromActivity:
    """Test the DELETE /activities/{activity_name}/signup endpoint"""

    def test_unregister_valid_participant(self):
        """Test unregistering a participant"""
        email = "unregister@mergington.edu"
        activity = "Drama Club"
        
        # First, sign up
        client.post(f"/activities/{activity}/signup?email={email}")
        
        # Verify they're registered
        response_before = client.get("/activities")
        assert email in response_before.json()[activity]["participants"]
        
        # Unregister
        response = client.delete(
            f"/activities/{activity}/signup?email={email}"
        )
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]
        
        # Verify they're no longer registered
        response_after = client.get("/activities")
        assert email not in response_after.json()[activity]["participants"]

    def test_unregister_invalid_activity_returns_404(self):
        """Test unregistering from non-existent activity returns 404"""
        response = client.delete(
            "/activities/NonExistentActivity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_non_registered_participant_returns_400(self):
        """Test unregistering a non-registered participant returns 400"""
        response = client.delete(
            "/activities/Basketball/signup?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]


class TestIntegration:
    """Integration tests for the complete workflow"""

    def test_complete_signup_workflow(self):
        """Test the complete workflow: get activities, sign up, and unregister"""
        email = "workflow@mergington.edu"
        activity = "Robotics Club"
        
        # Step 1: Get activities
        response = client.get("/activities")
        assert response.status_code == 200
        initial_participants = len(response.json()[activity]["participants"])
        
        # Step 2: Sign up
        signup_response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert signup_response.status_code == 200
        
        # Step 3: Verify signup
        response = client.get("/activities")
        assert len(response.json()[activity]["participants"]) == initial_participants + 1
        assert email in response.json()[activity]["participants"]
        
        # Step 4: Unregister
        unregister_response = client.delete(
            f"/activities/{activity}/signup?email={email}"
        )
        assert unregister_response.status_code == 200
        
        # Step 5: Verify unregister
        response = client.get("/activities")
        assert len(response.json()[activity]["participants"]) == initial_participants
        assert email not in response.json()[activity]["participants"]
