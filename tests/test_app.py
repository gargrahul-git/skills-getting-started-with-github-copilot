import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def test_activities(monkeypatch):
    activities = {
        "Robotics Club": {
            "description": "Build and program robots",
            "schedule": "Mondays, 3:30 PM - 5:00 PM",
            "max_participants": 10,
            "participants": ["existing@school.edu"],
        }
    }
    monkeypatch.setattr(app_module, "activities", activities)
    return activities


@pytest.fixture
def client(test_activities):
    return TestClient(app_module.app)


def test_root_redirects_to_static_index(client):
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_get_activities_returns_available_activities(client, test_activities):
    # Arrange

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == test_activities


def test_signup_adds_participant(client, test_activities):
    # Arrange
    email = "student@school.edu"

    # Act
    response = client.post(
        "/activities/Robotics%20Club/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Robotics Club"}
    assert test_activities["Robotics Club"]["participants"] == [
        "existing@school.edu",
        email,
    ]


def test_signup_rejects_duplicate_participant(client, test_activities):
    # Arrange
    email = "existing@school.edu"
    participants_before = test_activities["Robotics Club"]["participants"].copy()

    # Act
    response = client.post(
        "/activities/Robotics%20Club/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student is already signed up for this activity"
    }
    assert test_activities["Robotics Club"]["participants"] == participants_before


def test_signup_rejects_unknown_activity(client):
    # Arrange
    email = "student@school.edu"

    # Act
    response = client.post(
        "/activities/Unknown%20Club/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_remove_participant_from_activity(client, test_activities):
    # Arrange
    email = "existing@school.edu"

    # Act
    response = client.delete(
        "/activities/Robotics%20Club/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from Robotics Club"}
    assert test_activities["Robotics Club"]["participants"] == []


def test_remove_participant_from_unknown_activity_returns_not_found(client):
    # Arrange
    email = "student@school.edu"

    # Act
    response = client.delete(
        "/activities/Unknown%20Club/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_remove_unregistered_participant_returns_not_found(client):
    # Arrange
    email = "student@school.edu"

    # Act
    response = client.delete(
        "/activities/Robotics%20Club/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student is not signed up for this activity"
    }