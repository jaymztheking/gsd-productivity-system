"""API tests for areas of focus (TASK-016).

    PYTHONPATH=api pytest api/tests/test_areas.py -v
"""

import uuid


def _area(client, name):
    res = client.post("/areas", json={"name": name})
    assert res.status_code == 201, res.text
    return res.json()


def _names(client):
    res = client.get("/areas")
    assert res.status_code == 200, res.text
    return [a["name"] for a in res.json()]


def _project(client, name, **fields):
    res = client.post("/projects", json={"name": name, **fields})
    assert res.status_code == 201, res.text
    return res.json()


def _task(client, title, **fields):
    res = client.post("/next-actions", json={"title": title, **fields})
    assert res.status_code == 201, res.text
    return res.json()


def _get_task(client, task_id):
    res = client.get("/next-actions")
    return next(t for t in res.json() if t["id"] == task_id)


# --- Area CRUD and order ---------------------------------------------------


def test_new_areas_are_listed_in_creation_order(api_client):
    _area(api_client, "Home life")
    _area(api_client, "Professional development")
    _area(api_client, "Health")
    assert _names(api_client) == ["Home life", "Professional development", "Health"]


def test_area_can_be_renamed(api_client):
    area = _area(api_client, "Home")
    res = api_client.patch(f"/areas/{area['id']}", json={"name": "Home life"})
    assert res.status_code == 200, res.text
    assert _names(api_client) == ["Home life"]


def test_area_names_are_unique_and_not_blank(api_client):
    area = _area(api_client, "Home life")
    _area(api_client, "Health")
    assert api_client.post("/areas", json={"name": "Home life"}).status_code == 409
    assert (
        api_client.patch(f"/areas/{area['id']}", json={"name": "Health"}).status_code
        == 409
    )
    assert api_client.post("/areas", json={"name": "   "}).status_code == 422


def test_reorder_persists(api_client):
    home = _area(api_client, "Home life")
    work = _area(api_client, "Professional development")
    health = _area(api_client, "Health")
    res = api_client.put(
        "/areas/order", json={"ordered_ids": [health["id"], home["id"], work["id"]]}
    )
    assert res.status_code == 204, res.text
    assert _names(api_client) == ["Health", "Home life", "Professional development"]


def test_reorder_must_list_every_area_once(api_client):
    home = _area(api_client, "Home life")
    work = _area(api_client, "Professional development")
    for ids in (
        [home["id"]],
        [home["id"], home["id"]],
        [home["id"], work["id"], str(uuid.uuid4())],
    ):
        res = api_client.put("/areas/order", json={"ordered_ids": ids})
        assert res.status_code == 422, ids
    assert _names(api_client) == ["Home life", "Professional development"]


def test_unknown_area_is_404(api_client):
    missing = uuid.uuid4()
    assert api_client.patch(f"/areas/{missing}", json={"name": "x"}).status_code == 404
    assert api_client.delete(f"/areas/{missing}").status_code == 404


# --- Assignment --------------------------------------------------------------


def test_task_and_project_take_one_area(api_client):
    home = _area(api_client, "Home life")
    work = _area(api_client, "Professional development")
    task = _task(api_client, "Fix the tap", status="active", area_id=home["id"])
    project = _project(api_client, "Get certified", area_id=work["id"])
    assert task["area_id"] == home["id"]
    assert project["area_id"] == work["id"]

    res = api_client.patch(f"/next-actions/{task['id']}", json={"area_id": work["id"]})
    assert res.json()["area_id"] == work["id"]
    res = api_client.patch(f"/projects/{project['id']}", json={"area_id": None})
    assert res.json()["area_id"] is None


def test_patch_without_area_leaves_it_alone(api_client):
    home = _area(api_client, "Home life")
    task = _task(api_client, "Fix the tap", area_id=home["id"])
    res = api_client.patch(f"/next-actions/{task['id']}", json={"title": "Fix taps"})
    assert res.json()["area_id"] == home["id"]


def test_unknown_area_id_is_rejected(api_client):
    missing = str(uuid.uuid4())
    res = api_client.post("/next-actions", json={"title": "x", "area_id": missing})
    assert res.status_code == 422
    res = api_client.post("/projects", json={"name": "x", "area_id": missing})
    assert res.status_code == 422


# --- Tasks in a project take the project's area (TASK-021) -------------------


def _patch(client, task, **fields):
    return client.patch(f"/next-actions/{task['id']}", json=fields)


def test_task_in_project_has_project_area(api_client):
    work = _area(api_client, "Professional development")
    project = _project(api_client, "Get certified", area_id=work["id"])
    task = _task(api_client, "Book the exam", project_id=project["id"])
    assert task["area_id"] == work["id"]


def test_task_in_project_without_area_has_none(api_client):
    _area(api_client, "Home life")
    project = _project(api_client, "Renovate kitchen")
    task = _task(api_client, "Measure walls", project_id=project["id"])
    assert task["area_id"] is None


def test_area_sent_on_create_loses_to_the_project(api_client):
    home = _area(api_client, "Home life")
    work = _area(api_client, "Professional development")
    project = _project(api_client, "Get certified", area_id=work["id"])
    for area_id in (home["id"], None):
        task = _task(
            api_client, "Clear the desk", project_id=project["id"], area_id=area_id
        )
        assert task["area_id"] == work["id"]


def test_changing_project_area_moves_its_tasks(api_client):
    home = _area(api_client, "Home life")
    work = _area(api_client, "Professional development")
    project = _project(api_client, "Get certified", area_id=work["id"])
    other = _project(api_client, "Renovate kitchen", area_id=home["id"])
    a = _task(api_client, "Book the exam", project_id=project["id"])
    b = _task(api_client, "Buy study guide", project_id=project["id"])
    c = _task(api_client, "Measure walls", project_id=other["id"])
    loose = _task(api_client, "Call bank", area_id=work["id"])

    res = api_client.patch(f"/projects/{project['id']}", json={"area_id": home["id"]})
    assert res.status_code == 200, res.text
    for t in (a, b):
        assert _get_task(api_client, t["id"])["area_id"] == home["id"]
    # Tasks outside the project are untouched
    assert _get_task(api_client, c["id"])["area_id"] == home["id"]
    assert _get_task(api_client, loose["id"])["area_id"] == work["id"]

    api_client.patch(f"/projects/{project['id']}", json={"area_id": None})
    for t in (a, b):
        assert _get_task(api_client, t["id"])["area_id"] is None


def test_different_area_on_project_task_is_refused(api_client):
    home = _area(api_client, "Home life")
    work = _area(api_client, "Professional development")
    project = _project(api_client, "Get certified", area_id=work["id"])
    task = _task(api_client, "Book the exam", project_id=project["id"])

    for area_id in (home["id"], None):
        res = _patch(api_client, task, area_id=area_id)
        assert res.status_code == 422, res.text
    assert _get_task(api_client, task["id"])["area_id"] == work["id"]
    # Re-sending the project's own area is harmless, as the editor does
    res = _patch(api_client, task, title="Book exam", area_id=work["id"])
    assert res.status_code == 200, res.text


def test_project_and_area_in_one_request_takes_project_area(api_client):
    home = _area(api_client, "Home life")
    work = _area(api_client, "Professional development")
    project = _project(api_client, "Get certified", area_id=work["id"])
    task = _task(api_client, "Clear the desk", area_id=home["id"])
    res = _patch(api_client, task, project_id=project["id"], area_id=home["id"])
    assert res.status_code == 200, res.text
    assert res.json()["area_id"] == work["id"]


def test_task_moved_into_project_takes_its_area(api_client):
    home = _area(api_client, "Home life")
    work = _area(api_client, "Professional development")
    project = _project(api_client, "Get certified", area_id=work["id"])
    loose = _task(api_client, "Book the exam")
    placed = _task(api_client, "Clear the desk", area_id=home["id"])
    for task in (loose, placed):
        res = _patch(api_client, task, project_id=project["id"])
        assert res.status_code == 200, res.text
        assert res.json()["area_id"] == work["id"]


def test_task_leaving_project_keeps_area_and_can_change_it(api_client):
    home = _area(api_client, "Home life")
    work = _area(api_client, "Professional development")
    project = _project(api_client, "Get certified", area_id=work["id"])
    task = _task(api_client, "Book the exam", project_id=project["id"])

    res = _patch(api_client, task, project_id=None)
    assert res.status_code == 200, res.text
    assert res.json()["project_id"] is None
    assert res.json()["area_id"] == work["id"]

    res = _patch(api_client, task, area_id=home["id"])
    assert res.status_code == 200, res.text
    assert res.json()["area_id"] == home["id"]


def test_task_keeps_area_when_its_project_is_deleted(api_client):
    work = _area(api_client, "Professional development")
    project = _project(api_client, "Get certified", area_id=work["id"])
    task = _task(api_client, "Book the exam", project_id=project["id"])
    assert api_client.delete(f"/projects/{project['id']}").status_code == 204
    after = _get_task(api_client, task["id"])
    assert after["project_id"] is None
    assert after["area_id"] == work["id"]


def test_unknown_project_is_rejected(api_client):
    missing = str(uuid.uuid4())
    res = api_client.post("/next-actions", json={"title": "x", "project_id": missing})
    assert res.status_code == 422
    task = _task(api_client, "x")
    assert _patch(api_client, task, project_id=missing).status_code == 422


def test_deleting_area_unassigns_tasks_and_projects(api_client):
    home = _area(api_client, "Home life")
    task = _task(api_client, "Fix the tap", area_id=home["id"])
    project = _project(api_client, "Renovate kitchen", area_id=home["id"])

    assert api_client.delete(f"/areas/{home['id']}").status_code == 204
    assert _names(api_client) == []
    assert _get_task(api_client, task["id"])["area_id"] is None
    res = api_client.get(f"/projects/{project['id']}")
    assert res.status_code == 200
    assert res.json()["area_id"] is None
