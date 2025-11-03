import copy
import importlib

from fastapi.testclient import TestClient
import pytest


# Import the running app module dynamically
app_module = importlib.import_module("src.app")
app = app_module.app

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset the in-memory activities dict before/after each test to keep tests isolated."""
    original = copy.deepcopy(app_module.activities)
    yield
    app_module.activities.clear()
    app_module.activities.update(original)


def test_get_activities():
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    # sanity check one known activity exists
    assert "Chess Club" in data


def test_signup_and_unregister_flow():
    activity = "Robotics Club"
    email = "teststudent@example.com"

    # Ensure the test email is not already signed up
    resp = client.get("/activities")
    assert email not in resp.json()[activity]["participants"]

    # Sign up
    resp = client.post(f"/activities/{activity}/signup?email={email}")
    assert resp.status_code == 200
    assert "Signed up" in resp.json()["message"]

    # Verify participant present
    resp = client.get("/activities")
    assert email in resp.json()[activity]["participants"]

    # Signing up again should fail with 400
    resp = client.post(f"/activities/{activity}/signup?email={email}")
    assert resp.status_code == 400

    # Unregister
    resp = client.delete(f"/activities/{activity}/unregister?email={email}")
    assert resp.status_code == 200
    assert "Unregistered" in resp.json()["message"]

    # Confirm removal
    resp = client.get("/activities")
    assert email not in resp.json()[activity]["participants"]


def test_unregister_nonexistent_returns_404():
    activity = "Robotics Club"
    email = "noone@example.com"
    resp = client.delete(f"/activities/{activity}/unregister?email={email}")
    assert resp.status_code == 404
