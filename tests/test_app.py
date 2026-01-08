from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


def test_get_activities_contains_known_activities():
    r = client.get("/activities")
    assert r.status_code == 200
    data = r.json()
    assert "Basketball" in data
    assert "Chess Club" in data
    # Chess Club has two seeded participants
    assert "michael@mergington.edu" in data["Chess Club"]["participants"]


def test_signup_and_unregister_flow():
    # pick Basketball activity (stable id from slugify)
    r = client.get("/activities")
    assert r.status_code == 200
    activities = r.json()
    activity_name = "Basketball"
    activity_id = activities[activity_name]["id"]

    email = "pytest-user@example.com"

    # ensure clean start
    assert email not in activities[activity_name]["participants"]

    # signup
    r = client.post(f"/activities/{activity_id}/signup?email={email}")
    assert r.status_code == 200
    assert "Signed up" in r.json().get("message", "")

    # verify participant appears in GET /activities
    r = client.get("/activities")
    assert r.status_code == 200
    activities = r.json()
    assert email in activities[activity_name]["participants"]

    # double signup should fail
    r = client.post(f"/activities/{activity_id}/signup?email={email}")
    assert r.status_code == 400

    # unregister
    r = client.delete(f"/activities/{activity_id}/participants?email={email}")
    assert r.status_code == 200
    assert "Unregistered" in r.json().get("message", "")

    # verify removal
    r = client.get("/activities")
    activities = r.json()
    assert email not in activities[activity_name]["participants"]

    # unregistering again returns 404
    r = client.delete(f"/activities/{activity_id}/participants?email={email}")
    assert r.status_code == 404


def test_resolve_by_slug_and_case_insensitive():
    # use slug for Programming Class (programming-class) and case-insensitive name
    email1 = "slug-test@example.com"
    email2 = "case-test@example.com"

    r = client.post(f"/activities/programming-class/signup?email={email1}")
    assert r.status_code == 200

    r = client.post(f"/activities/Programming Class/signup?email={email2}")
    assert r.status_code == 200

    # verify both present
    r = client.get("/activities")
    activities = r.json()
    participants = activities["Programming Class"]["participants"]
    assert email1 in participants
    assert email2 in participants

    # cleanup
    client.delete(f"/activities/programming-class/participants?email={email1}")
    client.delete(f"/activities/programming-class/participants?email={email2}")
