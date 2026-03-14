"""
Integration tests for the weekly digest data pipeline.
Creates real test data for each digest section, verifies it appears correctly,
then cleans up.

Run against live k3s:
    API_URL=http://gsd.home.lab/api pytest api/tests/test_digest_pipeline.py -v

Run against local dev:
    pytest api/tests/test_digest_pipeline.py -v
"""

import os
import pytest
import requests

API_URL = os.getenv("API_URL", "http://localhost:8000")
NEXT_ACTIONS = f"{API_URL}/next-actions"
PROJECTS = f"{API_URL}/projects"

# Tag IDs (seeded, stable)
TAG_SOMEDAY = "9be1dbbc-1c0b-5c47-ac93-ae64bdbe7bdb"

TEST_PREFIX = "[DIGEST-TEST]"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def create_action(title, status="inbox", tag_ids=None, project_id=None):
    payload = {"title": f"{TEST_PREFIX} {title}", "status": status}
    if tag_ids:
        payload["tag_ids"] = tag_ids
    if project_id:
        payload["project_id"] = project_id
    resp = requests.post(NEXT_ACTIONS, json=payload)
    resp.raise_for_status()
    return resp.json()


def create_project(name):
    resp = requests.post(PROJECTS, json={"name": f"{TEST_PREFIX} {name}"})
    resp.raise_for_status()
    return resp.json()


def delete_action(id):
    requests.delete(f"{NEXT_ACTIONS}/{id}")


def delete_project(id):
    requests.delete(f"{PROJECTS}/{id}")


def get_actions(status):
    resp = requests.get(NEXT_ACTIONS, params={"status": status})
    resp.raise_for_status()
    return resp.json()


def get_projects(status="active"):
    resp = requests.get(PROJECTS, params={"status": status})
    resp.raise_for_status()
    return resp.json()


@pytest.fixture(autouse=True)
def cleanup_test_data():
    """Remove leftover test data before and after every test."""
    def _cleanup():
        for status in ("inbox", "active", "pending"):
            for item in get_actions(status):
                if item["title"].startswith(TEST_PREFIX):
                    delete_action(item["id"])
        for project in get_projects():
            if project["name"].startswith(TEST_PREFIX):
                delete_project(project["id"])

    _cleanup()
    yield
    _cleanup()


# ---------------------------------------------------------------------------
# Inbox section
# ---------------------------------------------------------------------------

def test_inbox_item_appears_in_digest_inbox_section():
    item = create_action("inbox task", status="inbox")
    inbox = get_actions("inbox")
    ids = [i["id"] for i in inbox]
    assert item["id"] in ids, "Inbox item not found in inbox endpoint"


def test_inbox_item_excluded_from_active_and_pending():
    item = create_action("inbox only", status="inbox")
    for status in ("active", "pending"):
        ids = [i["id"] for i in get_actions(status)]
        assert item["id"] not in ids, f"Inbox item leaked into {status}"


# ---------------------------------------------------------------------------
# Active Actions section
# ---------------------------------------------------------------------------

def test_active_item_appears_in_digest_active_section():
    item = create_action("active task", status="active")
    ids = [i["id"] for i in get_actions("active")]
    assert item["id"] in ids, "Active item not found in active endpoint"


def test_active_item_has_fields_digest_needs():
    item = create_action("field check", status="active")
    active = get_actions("active")
    match = next(i for i in active if i["id"] == item["id"])
    for field in ("id", "title", "status", "tags", "updated_at", "project_id"):
        assert field in match, f"Missing field: {field}"


# ---------------------------------------------------------------------------
# Pending / Waiting For section
# ---------------------------------------------------------------------------

def test_pending_item_appears_in_digest_pending_section():
    item = create_action("waiting for response", status="pending")
    ids = [i["id"] for i in get_actions("pending")]
    assert item["id"] in ids, "Pending item not found in pending endpoint"


def test_pending_item_excluded_from_inbox_and_active():
    item = create_action("pending only", status="pending")
    for status in ("inbox", "active"):
        ids = [i["id"] for i in get_actions(status)]
        assert item["id"] not in ids, f"Pending item leaked into {status}"


# ---------------------------------------------------------------------------
# Someday / Maybe section (active items tagged #someday)
# ---------------------------------------------------------------------------

def test_someday_item_appears_in_active_with_someday_tag():
    item = create_action("someday idea", status="active", tag_ids=[TAG_SOMEDAY])
    active = get_actions("active")
    match = next((i for i in active if i["id"] == item["id"]), None)
    assert match is not None, "Someday item not found in active endpoint"
    tag_names = [t["name"] for t in match["tags"]]
    assert "#someday" in tag_names, "#someday tag not present on item"


def test_active_item_without_someday_tag_not_in_someday_section():
    item = create_action("regular active task", status="active")
    active = get_actions("active")
    match = next((i for i in active if i["id"] == item["id"]), None)
    assert match is not None
    tag_names = [t["name"] for t in match["tags"]]
    assert "#someday" not in tag_names


# ---------------------------------------------------------------------------
# Active Projects section
# ---------------------------------------------------------------------------

def test_active_project_appears_in_digest_projects_section():
    project = create_project("test project")
    ids = [p["id"] for p in get_projects("active")]
    assert project["id"] in ids, "Active project not found in projects endpoint"


def test_project_with_next_action_linkable():
    project = create_project("project with action")
    action = create_action("next action for project", status="active", project_id=project["id"])
    active = get_actions("active")
    match = next((i for i in active if i["id"] == action["id"]), None)
    assert match is not None
    assert match["project_id"] == project["id"], "Action not linked to project"


def test_project_without_next_action_detectable():
    project = create_project("project no actions")
    active = get_actions("active")
    project_ids_with_actions = {i["project_id"] for i in active if i["project_id"]}
    assert project["id"] not in project_ids_with_actions, \
        "Project incorrectly shows as having a next action"
