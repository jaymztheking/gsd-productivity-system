"""API tests for the someday next-action status (TASK-014).

Someday/Maybe used to be active items tagged #someday, so they showed up in
Engage and in the digest's active list. It is now a status of its own.

    PYTHONPATH=api pytest api/tests/test_someday.py -v
"""


def _create(client, title, status):
    res = client.post("/next-actions", json={"title": title, "status": status})
    assert res.status_code == 201, res.text
    return res.json()


def _titles(client, status):
    res = client.get("/next-actions", params={"status": status})
    assert res.status_code == 200, res.text
    return {a["title"] for a in res.json()}


def test_someday_items_are_listed_only_under_someday(api_client):
    _create(api_client, "Learn Italian", "someday")
    _create(api_client, "Call dentist", "active")
    _create(api_client, "Hear back from plumber", "pending")

    assert _titles(api_client, "someday") == {"Learn Italian"}
    # Engage loads active and pending; the digest loads both plus someday
    assert _titles(api_client, "active") == {"Call dentist"}
    assert _titles(api_client, "pending") == {"Hear back from plumber"}


def test_inbox_item_can_be_filed_to_someday(api_client):
    item = _create(api_client, "Maybe build a shed", "inbox")
    res = api_client.patch(
        f"/next-actions/{item['id']}", json={"status": "someday"}
    )
    assert res.status_code == 200, res.text
    assert res.json()["status"] == "someday"
    assert _titles(api_client, "inbox") == set()
    assert _titles(api_client, "someday") == {"Maybe build a shed"}


def test_someday_item_can_be_promoted_to_active(api_client):
    item = _create(api_client, "Learn Italian", "someday")
    res = api_client.patch(f"/next-actions/{item['id']}", json={"status": "active"})
    assert res.status_code == 200, res.text
    assert _titles(api_client, "someday") == set()
    assert _titles(api_client, "active") == {"Learn Italian"}


def test_deleted_someday_item_leaves_the_list(api_client):
    item = _create(api_client, "Learn Italian", "someday")
    res = api_client.delete(f"/next-actions/{item['id']}")
    assert res.status_code == 204, res.text
    assert _titles(api_client, "someday") == set()
