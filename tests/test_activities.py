"""Tests for the FastAPI activities API."""

import pytest


class TestRootEndpoint:
    """Tests for the root endpoint."""
    
    def test_root_redirects_to_static(self, client):
        """Test that GET / redirects to /static/index.html."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivitiesEndpoint:
    """Tests for the GET /activities endpoint."""
    
    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """Test that GET /activities returns all activities."""
        response = client.get("/activities")
        assert response.status_code == 200
        activities = response.json()
        
        # Verify all 9 activities are returned
        assert len(activities) == 9
        assert "Chess Club" in activities
        assert "Programming Class" in activities
        assert "Gym Class" in activities
        assert "Basketball Team" in activities
        assert "Tennis Club" in activities
        assert "Art Studio" in activities
        assert "Drama Club" in activities
        assert "Debate Team" in activities
        assert "Science Club" in activities
    
    def test_get_activities_structure(self, client, reset_activities):
        """Test that each activity has the required fields."""
        response = client.get("/activities")
        assert response.status_code == 200
        activities = response.json()
        
        # Check structure of each activity
        for activity_name, activity_data in activities.items():
            assert isinstance(activity_data, dict)
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)
    
    def test_get_activities_initial_participants(self, client, reset_activities):
        """Test that activities have the correct initial participants."""
        response = client.get("/activities")
        activities = response.json()
        
        # Verify some known participants
        assert "michael@mergington.edu" in activities["Chess Club"]["participants"]
        assert "emma@mergington.edu" in activities["Programming Class"]["participants"]
        assert "john@mergington.edu" in activities["Gym Class"]["participants"]


class TestSignupEndpoint:
    """Tests for the POST /activities/{activity_name}/signup endpoint."""
    
    def test_signup_success(self, client, reset_activities):
        """Test successful signup for an activity."""
        email = "newemail@mergington.edu"
        activity = "Chess Club"
        
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity in data["message"]
    
    def test_signup_updates_participants_list(self, client, reset_activities):
        """Test that new participant appears in activities after signup."""
        email = "newemail@mergington.edu"
        activity = "Chess Club"
        
        # Verify email is not in participants yet
        response = client.get("/activities")
        activities = response.json()
        assert email not in activities[activity]["participants"]
        
        # Signup
        signup_response = client.post(f"/activities/{activity}/signup?email={email}")
        assert signup_response.status_code == 200
        
        # Verify email is now in participants
        response = client.get("/activities")
        activities = response.json()
        assert email in activities[activity]["participants"]
    
    def test_signup_duplicate_participant_fails(self, client, reset_activities):
        """Test that signing up the same email twice returns 400."""
        email = "michael@mergington.edu"  # Already participant in Chess Club
        activity = "Chess Club"
        
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data
        assert "already signed up" in data["detail"].lower()
    
    def test_signup_invalid_activity_fails(self, client, reset_activities):
        """Test that signing up for non-existent activity returns 404."""
        email = "newemail@mergington.edu"
        activity = "Non-existent Activity"
        
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
    
    def test_signup_multiple_activities(self, client, reset_activities):
        """Test that same email can signup for multiple different activities."""
        email = "newemail@mergington.edu"
        
        # Signup for Chess Club
        response1 = client.post(f"/activities/Chess Club/signup?email={email}")
        assert response1.status_code == 200
        
        # Signup for Programming Class
        response2 = client.post(f"/activities/Programming Class/signup?email={email}")
        assert response2.status_code == 200
        
        # Verify email is in both activities
        response = client.get("/activities")
        activities = response.json()
        assert email in activities["Chess Club"]["participants"]
        assert email in activities["Programming Class"]["participants"]


class TestUnregisterEndpoint:
    """Tests for the DELETE /activities/{activity_name}/unregister endpoint."""
    
    def test_unregister_success(self, client, reset_activities):
        """Test successful unregister from an activity."""
        email = "michael@mergington.edu"
        activity = "Chess Club"
        
        response = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity in data["message"]
    
    def test_unregister_removes_from_participants_list(self, client, reset_activities):
        """Test that participant is removed from activities after unregister."""
        email = "michael@mergington.edu"
        activity = "Chess Club"
        
        # Verify email is in participants
        response = client.get("/activities")
        activities = response.json()
        assert email in activities[activity]["participants"]
        
        # Unregister
        unregister_response = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert unregister_response.status_code == 200
        
        # Verify email is no longer in participants
        response = client.get("/activities")
        activities = response.json()
        assert email not in activities[activity]["participants"]
    
    def test_unregister_invalid_activity_fails(self, client, reset_activities):
        """Test that unregistering from non-existent activity returns 404."""
        email = "michael@mergington.edu"
        activity = "Non-existent Activity"
        
        response = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
    
    def test_unregister_non_participant_fails(self, client, reset_activities):
        """Test that unregistering someone not signed up returns 400."""
        email = "notregistered@mergington.edu"
        activity = "Chess Club"
        
        response = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data
        assert "not signed up" in data["detail"].lower()
    
    def test_unregister_then_signup_again(self, client, reset_activities):
        """Test that a participant can unregister and sign up again."""
        email = "michael@mergington.edu"
        activity = "Chess Club"
        
        # Unregister
        response1 = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert response1.status_code == 200
        
        # Verify email is not in participants
        response = client.get("/activities")
        activities = response.json()
        assert email not in activities[activity]["participants"]
        
        # Sign up again
        response2 = client.post(f"/activities/{activity}/signup?email={email}")
        assert response2.status_code == 200
        
        # Verify email is back in participants
        response = client.get("/activities")
        activities = response.json()
        assert email in activities[activity]["participants"]


class TestIntegration:
    """Integration tests combining multiple operations."""
    
    def test_signup_and_unregister_workflow(self, client, reset_activities):
        """Test complete workflow of signup and unregister."""
        email = "integrationtest@mergington.edu"
        activity = "Art Studio"
        
        # Initial state - email not in participants
        response = client.get("/activities")
        assert email not in response.json()[activity]["participants"]
        
        # Signup
        signup_response = client.post(f"/activities/{activity}/signup?email={email}")
        assert signup_response.status_code == 200
        
        # Verify signup worked
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]
        
        # Unregister
        unregister_response = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert unregister_response.status_code == 200
        
        # Verify unregister worked
        response = client.get("/activities")
        assert email not in response.json()[activity]["participants"]
    
    def test_multiple_participants_management(self, client, reset_activities):
        """Test managing multiple participants in an activity."""
        activity = "Debate Team"
        
        # Get initial participant count
        response = client.get("/activities")
        initial_count = len(response.json()[activity]["participants"])
        
        # Signup 3 new participants
        emails = ["user1@mergington.edu", "user2@mergington.edu", "user3@mergington.edu"]
        for email in emails:
            signup_response = client.post(f"/activities/{activity}/signup?email={email}")
            assert signup_response.status_code == 200
        
        # Verify all 3 are added
        response = client.get("/activities")
        assert len(response.json()[activity]["participants"]) == initial_count + 3
        
        # Unregister 2 of them
        for email in emails[:2]:
            unregister_response = client.delete(f"/activities/{activity}/unregister?email={email}")
            assert unregister_response.status_code == 200
        
        # Verify only 1 new participant remains
        response = client.get("/activities")
        assert len(response.json()[activity]["participants"]) == initial_count + 1
        assert emails[2] in response.json()[activity]["participants"]
