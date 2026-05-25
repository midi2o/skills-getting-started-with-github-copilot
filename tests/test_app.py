"""FastAPI endpoint tests using the AAA (Arrange-Act-Assert) pattern."""

import pytest


class TestRootEndpoint:
    """Tests for the root endpoint."""
    
    def test_root_redirects_to_static_index_html(self, client):
        """
        GIVEN: A request to the root endpoint
        WHEN: The client makes a GET request to /
        THEN: The response should redirect to /static/index.html with status 307
        """
        # Arrange
        expected_redirect_url = "/static/index.html"
        
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == expected_redirect_url


class TestGetActivitiesEndpoint:
    """Tests for the GET /activities endpoint."""
    
    def test_get_activities_returns_all_activities(self, client):
        """
        GIVEN: The activities database is populated with 9 activities
        WHEN: The client makes a GET request to /activities
        THEN: The response should contain all 9 activities with correct structure
        """
        # Arrange
        expected_activity_count = 9
        expected_activity_names = [
            "Chess Club", "Programming Class", "Gym Class", "Basketball Team",
            "Tennis Club", "Art Studio", "Music Band", "Debate Club", "Science Club"
        ]
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        activities = response.json()
        assert len(activities) == expected_activity_count
        assert set(activities.keys()) == set(expected_activity_names)
    
    def test_get_activities_response_contains_required_fields(self, client):
        """
        GIVEN: A request to fetch all activities
        WHEN: The client makes a GET request to /activities
        THEN: Each activity should have description, schedule, max_participants, and participants
        """
        # Arrange
        required_fields = {"description", "schedule", "max_participants", "participants"}
        
        # Act
        response = client.get("/activities")
        activities = response.json()
        
        # Assert
        for activity_name, activity_data in activities.items():
            assert set(activity_data.keys()) == required_fields, \
                f"Activity {activity_name} missing required fields"
            assert isinstance(activity_data["participants"], list)
            assert isinstance(activity_data["max_participants"], int)
    
    def test_get_activities_has_cache_control_no_store_header(self, client):
        """
        GIVEN: A request to fetch all activities
        WHEN: The client makes a GET request to /activities
        THEN: The response should include Cache-Control: no-store header
        """
        # Arrange
        expected_cache_control = "no-store"
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert "cache-control" in response.headers
        assert response.headers["cache-control"] == expected_cache_control


class TestSignupEndpoint:
    """Tests for the POST /activities/{activity_name}/signup endpoint."""
    
    def test_signup_succeeds_for_valid_activity_and_email(self, client):
        """
        GIVEN: A student email that is not yet signed up for an activity
        WHEN: The client makes a POST request to signup
        THEN: The signup should succeed with status 200 and confirmation message
        """
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
        assert email in response.json()["message"]
    
    def test_signup_adds_student_to_participants_list(self, client):
        """
        GIVEN: A student successfully signs up for an activity
        WHEN: The client fetches the activity details
        THEN: The student's email should be in the participants list
        """
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"
        
        # Act
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        activities_response = client.get("/activities")
        
        # Assert
        assert signup_response.status_code == 200
        activities = activities_response.json()
        assert email in activities[activity_name]["participants"]
    
    def test_signup_fails_for_nonexistent_activity(self, client):
        """
        GIVEN: A request to signup for an activity that does not exist
        WHEN: The client makes a POST request to signup for that activity
        THEN: The response should return 404 status with 'Activity not found' detail
        """
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"
    
    def test_signup_fails_when_student_already_enrolled(self, client):
        """
        GIVEN: A student who is already signed up for an activity
        WHEN: The client attempts to sign up the same student again
        THEN: The response should return 400 status with 'Student already signed up' detail
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already in Chess Club participants
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Student already signed up"
    
    def test_signup_fails_when_activity_is_full(self, client):
        """
        GIVEN: An activity that has reached max_participants capacity
        WHEN: The client attempts to signup another student
        THEN: The response should return 400 status with 'Activity is full' detail
        """
        # Arrange
        # Create a full activity by signing up students until capacity is reached
        activity_name = "Basketball Team"  # max_participants: 15
        # Currently has 1 participant, so add 14 more to reach 15
        for i in range(14):
            client.post(
                f"/activities/{activity_name}/signup",
                params={"email": f"filler{i}@mergington.edu"}
            )
        
        # Now the activity is full, attempt to add one more
        email = "overfull@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Activity is full"


class TestUnregisterEndpoint:
    """Tests for the DELETE /activities/{activity_name}/signup endpoint."""
    
    def test_unregister_succeeds_for_enrolled_student(self, client):
        """
        GIVEN: A student who is currently enrolled in an activity
        WHEN: The client makes a DELETE request to unregister
        THEN: The unregister should succeed with status 200 and confirmation message
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already in Chess Club participants
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]
        assert email in response.json()["message"]
    
    def test_unregister_removes_student_from_participants_list(self, client):
        """
        GIVEN: A student successfully unregisters from an activity
        WHEN: The client fetches the activity details
        THEN: The student's email should no longer be in the participants list
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        
        # Act
        unregister_response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        activities_response = client.get("/activities")
        
        # Assert
        assert unregister_response.status_code == 200
        activities = activities_response.json()
        assert email not in activities[activity_name]["participants"]
    
    def test_unregister_fails_for_nonexistent_activity(self, client):
        """
        GIVEN: A request to unregister from an activity that does not exist
        WHEN: The client makes a DELETE request to unregister
        THEN: The response should return 404 status with 'Activity not found' detail
        """
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"
    
    def test_unregister_fails_when_student_not_enrolled(self, client):
        """
        GIVEN: A student who is not enrolled in an activity
        WHEN: The client attempts to unregister them
        THEN: The response should return 400 status with 'Student is not signed up' detail
        """
        # Arrange
        activity_name = "Chess Club"
        email = "notmember@mergington.edu"  # Not in Chess Club participants
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Student is not signed up for this activity"


class TestStateIsolation:
    """Tests to verify that tests do not pollute shared state."""
    
    def test_multiple_signups_and_unregisters_in_sequence(self, client):
        """
        GIVEN: Multiple signup and unregister operations
        WHEN: The client performs these operations in sequence
        THEN: The activity participants list should reflect the correct final state
        """
        # Arrange
        activity_name = "Programming Class"
        email1 = "student1@mergington.edu"
        email2 = "student2@mergington.edu"
        
        # Act
        # First signup
        response1 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email1}
        )
        
        # Second signup
        response2 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email2}
        )
        
        # First unregister
        response3 = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email1}
        )
        
        # Check final state
        final_response = client.get("/activities")
        
        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response3.status_code == 200
        
        participants = final_response.json()[activity_name]["participants"]
        assert email1 not in participants
        assert email2 in participants
