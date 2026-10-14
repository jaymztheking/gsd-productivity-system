"""API tests for the manual Engage order (TASK-015).

    PYTHONPATH=api pytest api/tests/test_engage_order.py -v
"""

import uuid


def _task(client, title, status="active", **fields):
    res = client.post(
        "/next-actions", json={"title": title, "status": status, **fields}
    )
    assert res.status_code == 201, res.text
    return res.json()


def _order(client, status="active", **params):
    res = client.get("/next-actions", params={"status": status, **params})
    assert res.status_code == 200, res.text
    return [t["title"] for t in res.json()]


def _engage(client):
    """Active and pending together, as Engage shows them with Show Pending on."""
    res = [*_full(client, "active"), *_full(client, "pending")]
    return [t["title"] for t in sorted(res, key=lambda t: t["engage_sort_order"])]


def _full(client, status):
    return client.get("/next-actions", params={"status": status}).json()


def _reorder(client, *tasks):
    return client.put(
        "/next-actions/order", json={"ordered_ids": [t["id"] for t in tasks]}
    )


def test_new_tasks_go_to_the_bottom(api_client):
    for title in ("A", "B", "C"):
        _task(api_client, title)
    assert _order(api_client) == ["A", "B", "C"]


def test_full_reorder_persists(api_client):
    a, b, c = (_task(api_client, t) for t in "ABC")
    assert _reorder(api_client, c, a, b).status_code == 204
    assert _order(api_client) == ["C", "A", "B"]


def test_activated_task_goes_to_the_bottom(api_client):
    a, b = _task(api_client, "A"), _task(api_client, "B")
    _reorder(api_client, b, a)
    inbox = _task(api_client, "From inbox", status="inbox")
    someday = _task(api_client, "From someday", status="someday")
    for item in (inbox, someday):
        res = api_client.patch(
            f"/next-actions/{item['id']}", json={"status": "active"}
        )
        assert res.status_code == 200, res.text
    assert _order(api_client) == ["B", "A", "From inbox", "From someday"]


def test_switching_active_and_pending_keeps_the_place(api_client):
    a, b, c = (_task(api_client, t) for t in "ABC")
    api_client.patch(f"/next-actions/{b['id']}", json={"status": "pending"})
    assert _engage(api_client) == ["A", "B", "C"]
    api_client.patch(f"/next-actions/{b['id']}", json={"status": "active"})
    assert _order(api_client) == ["A", "B", "C"]


def test_pending_and_active_share_one_order(api_client):
    a = _task(api_client, "A")
    p = _task(api_client, "Waiting", status="pending")
    b = _task(api_client, "B")
    assert _reorder(api_client, p, b, a).status_code == 204
    assert _engage(api_client) == ["Waiting", "B", "A"]


def test_partial_reorder_keeps_hidden_tasks_in_place(api_client):
    # A filter shows only B and D; dragging D above B must not move A, C, E
    a, b, c, d, e = (_task(api_client, t) for t in "ABCDE")
    assert _reorder(api_client, d, b).status_code == 204
    assert _order(api_client) == ["A", "D", "C", "B", "E"]


def test_each_status_list_follows_the_order(api_client):
    a, b, c = (_task(api_client, t) for t in "ABC")
    p = _task(api_client, "P", status="pending")
    _reorder(api_client, p, c, b, a)
    assert _order(api_client, "pending") == ["P"]
    assert _order(api_client) == ["C", "B", "A"]


def test_inbox_stays_oldest_first(api_client):
    for title in ("First", "Second", "Third"):
        _task(api_client, title, status="inbox")
    assert _order(api_client, "inbox") == ["First", "Second", "Third"]


def test_invalid_id_lists_are_rejected_without_changes(api_client):
    a, b = _task(api_client, "A"), _task(api_client, "B")
    inbox = _task(api_client, "In inbox", status="inbox")
    deleted = _task(api_client, "Deleted")
    api_client.delete(f"/next-actions/{deleted['id']}")

    bad_lists = [
        [],
        [a["id"], a["id"]],
        [a["id"], str(uuid.uuid4())],
        [b["id"], inbox["id"]],
        [b["id"], deleted["id"]],
        ["not-a-uuid"],
    ]
    for ids in bad_lists:
        res = api_client.put("/next-actions/order", json={"ordered_ids": ids})
        assert res.status_code == 422, (ids, res.text)
    assert _order(api_client) == ["A", "B"]


def test_completed_tasks_leave_the_order(api_client):
    a, b, c = (_task(api_client, t) for t in "ABC")
    api_client.patch(f"/next-actions/{b['id']}", json={"status": "complete"})
    assert _reorder(api_client, c, a).status_code == 204
    assert _order(api_client) == ["C", "A"]
    # Reopening it places it at the bottom
    api_client.patch(f"/next-actions/{b['id']}", json={"status": "active"})
    assert _order(api_client) == ["C", "A", "B"]
