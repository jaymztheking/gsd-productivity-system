import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useProjectDetail } from "../hooks/useProjectDetail";
import { createProject } from "../api/client";
import LinkEditor from "../components/LinkEditor";
import ProjectTaskList from "../components/ProjectTaskList";
import type { ProjectStatus } from "../types/models";

export default function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const {
    project,
    tasks,
    history,
    loading,
    updateProject,
    deleteProject,
    addLink,
    editLink,
    removeLink,
    moveTask,
    refetch,
  } = useProjectDetail(id!);

  const [editingName, setEditingName] = useState(false);
  const [nameValue, setNameValue] = useState("");
  const [descValue, setDescValue] = useState("");
  const [editingDesc, setEditingDesc] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [showAddSub, setShowAddSub] = useState(false);
  const [subName, setSubName] = useState("");
  const [showHistory, setShowHistory] = useState(false);

  if (loading) {
    return <div className="loading">Loading project...</div>;
  }

  if (!project) {
    return (
      <div className="empty-state">
        <div className="empty-state__title">Project not found</div>
        <button className="btn btn--ghost" onClick={() => navigate("/projects")}>
          ← Back to Projects
        </button>
      </div>
    );
  }

  const handleNameSave = async () => {
    if (nameValue.trim() && nameValue.trim() !== project.name) {
      await updateProject({ name: nameValue.trim() });
    }
    setEditingName(false);
  };

  const handleDescSave = async () => {
    if (descValue !== (project.description || "")) {
      await updateProject({ description: descValue || null });
    }
    setEditingDesc(false);
  };

  const handleStatusToggle = async () => {
    const newStatus: ProjectStatus =
      project.status === "active" ? "complete" : "active";
    await updateProject({ status: newStatus });
  };

  const handleDelete = async () => {
    await deleteProject();
    navigate("/projects");
  };

  const handleAddSubProject = async () => {
    if (!subName.trim()) return;
    await createProject({
      name: subName.trim(),
      parent_id: project.id,
    });
    setSubName("");
    setShowAddSub(false);
    refetch();
  };

  // Only non-deleted, non-completed active tasks for the task list
  const activeTasks = tasks.filter(
    (t) => t.status !== "complete" && !t.deleted_at
  );

  return (
    <div className="stack stack--md">
      {/* Header */}
      <div className="project-header">
        <button
          className="btn btn--ghost"
          onClick={() =>
            project.parent_id
              ? navigate(`/projects/${project.parent_id}`)
              : navigate("/projects")
          }
        >
          ←
        </button>
        {editingName ? (
          <input
            className="input project-header__name-input"
            value={nameValue}
            onChange={(e) => setNameValue(e.target.value)}
            onBlur={handleNameSave}
            onKeyDown={(e) => e.key === "Enter" && handleNameSave()}
            autoFocus
          />
        ) : (
          <h2
            className="project-header__name"
            onClick={() => {
              setNameValue(project.name);
              setEditingName(true);
            }}
          >
            {project.name}
          </h2>
        )}
      </div>

      {/* Status toggle */}
      <div className="project-section">
        <button
          className={`btn ${
            project.status === "active" ? "btn--primary" : "btn--ghost"
          }`}
          onClick={handleStatusToggle}
        >
          {project.status === "active"
            ? "✓ Mark Complete"
            : "↩ Reactivate"}
        </button>
      </div>

      {/* Description */}
      <div className="project-section">
        <div className="project-section__label">Description</div>
        {editingDesc ? (
          <textarea
            className="input textarea"
            value={descValue}
            onChange={(e) => setDescValue(e.target.value)}
            onBlur={handleDescSave}
            rows={3}
            autoFocus
            placeholder="What is this project about?"
          />
        ) : (
          <div
            className="project-section__text"
            onClick={() => {
              setDescValue(project.description || "");
              setEditingDesc(true);
            }}
          >
            {project.description || (
              <span className="text-muted">Tap to add description...</span>
            )}
          </div>
        )}
      </div>

      {/* Links */}
      <div className="project-section">
        <div className="project-section__label">Links</div>
        <LinkEditor
          links={project.links}
          onAdd={addLink}
          onEdit={editLink}
          onRemove={removeLink}
        />
      </div>

      {/* Sub-projects (root projects only) */}
      {project.parent_id === null && (
        <div className="project-section">
          <div className="project-section__label">Sub-projects</div>
          {project.children.length === 0 && !showAddSub && (
            <div className="text-muted" style={{ fontSize: "0.85rem" }}>
              No sub-projects yet.
            </div>
          )}
          {project.children.map((child) => (
            <button
              key={child.id}
              className="card project-list-item"
              onClick={() => navigate(`/projects/${child.id}`)}
            >
              <div className="project-list-item__name">{child.name}</div>
            </button>
          ))}
          {showAddSub ? (
            <div className="stack stack--sm">
              <input
                className="input"
                placeholder="Sub-project name"
                value={subName}
                onChange={(e) => setSubName(e.target.value)}
                autoFocus
                onKeyDown={(e) => e.key === "Enter" && handleAddSubProject()}
              />
              <div className="btn-row">
                <button
                  className="btn btn--primary"
                  onClick={handleAddSubProject}
                  disabled={!subName.trim()}
                >
                  Add
                </button>
                <button
                  className="btn btn--ghost"
                  onClick={() => {
                    setShowAddSub(false);
                    setSubName("");
                  }}
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <button
              className="btn btn--ghost"
              onClick={() => setShowAddSub(true)}
            >
              + Add Sub-project
            </button>
          )}
        </div>
      )}

      {/* Active Tasks */}
      <div className="project-section">
        <div className="project-section__label">
          Tasks ({activeTasks.length})
        </div>
        <ProjectTaskList
          tasks={activeTasks}
          onMove={moveTask}
          onRefetch={refetch}
        />
      </div>

      {/* Task History */}
      <div className="project-section">
        <button
          className="btn btn--ghost section-toggle"
          onClick={() => setShowHistory(!showHistory)}
        >
          {showHistory ? "▾" : "▸"} Task History ({history.length})
        </button>
        {showHistory && (
          <div className="stack stack--xs">
            {history.length === 0 ? (
              <div className="text-muted" style={{ fontSize: "0.85rem" }}>
                No completed or removed tasks yet.
              </div>
            ) : (
              history.map((item) => (
                <div key={item.id} className="history-row">
                  <span
                    className={`history-row__icon ${
                      item.deleted_at
                        ? "history-row__icon--deleted"
                        : "history-row__icon--completed"
                    }`}
                  >
                    {item.deleted_at ? "✕" : "✓"}
                  </span>
                  <span
                    className={`history-row__title ${
                      item.deleted_at
                        ? "history-row__title--deleted"
                        : "history-row__title--completed"
                    }`}
                  >
                    {item.title}
                  </span>
                </div>
              ))
            )}
          </div>
        )}
      </div>

      {/* Danger zone */}
      <div className="danger-zone">
        {showDeleteConfirm ? (
          <div className="stack stack--sm">
            <p>
              Delete <strong>{project.name}</strong>?
              {activeTasks.length > 0 &&
                ` ${activeTasks.length} task(s) will become unassigned.`}
              {project.children.length > 0 &&
                ` ${project.children.length} sub-project(s) will become root projects.`}
            </p>
            <div className="btn-row">
              <button className="btn btn--danger" onClick={handleDelete}>
                Delete
              </button>
              <button
                className="btn btn--ghost"
                onClick={() => setShowDeleteConfirm(false)}
              >
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <button
            className="btn btn--danger-outline"
            onClick={() => setShowDeleteConfirm(true)}
          >
            Delete Project
          </button>
        )}
      </div>
    </div>
  );
}
