import { useState } from "react";
import { useNavigate } from "react-router-dom";
import AreaBadge from "../components/AreaBadge";
import AreaManager from "../components/AreaManager";
import { useAreas } from "../hooks/useAreas";
import { useProjects } from "../hooks/useProjects";
import type { Area, Project } from "../types/models";

export default function ProjectsPage() {
  const { projects, loading, createProject, refetch } = useProjects();
  const { areas, createArea, renameArea, deleteArea, moveArea } = useAreas();
  const navigate = useNavigate();
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [showCompleted, setShowCompleted] = useState(false);

  const active = projects.filter((p) => p.status === "active");
  const completed = projects.filter((p) => p.status === "complete");

  const handleCreate = async () => {
    if (!newName.trim()) return;
    const project = await createProject(newName.trim(), {
      description: newDesc.trim() || undefined,
    });
    setNewName("");
    setNewDesc("");
    setShowCreate(false);
    navigate(`/projects/${project.id}`);
  };

  if (loading) {
    return <div className="loading">Loading projects...</div>;
  }

  return (
    <div className="stack stack--md">
      <div className="project-list-header">
        <h2 className="page-title">Projects</h2>
        <button
          className="btn btn--primary"
          onClick={() => setShowCreate(!showCreate)}
        >
          {showCreate ? "Cancel" : "+ New Project"}
        </button>
      </div>

      {showCreate && (
        <div className="card">
          <div className="stack stack--sm">
            <input
              type="text"
              className="input"
              placeholder="Project name"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              autoFocus
              onKeyDown={(e) => e.key === "Enter" && handleCreate()}
            />
            <textarea
              className="input textarea"
              placeholder="Description (optional)"
              value={newDesc}
              onChange={(e) => setNewDesc(e.target.value)}
              rows={2}
            />
            <button
              className="btn btn--primary"
              onClick={handleCreate}
              disabled={!newName.trim()}
            >
              Create Project
            </button>
          </div>
        </div>
      )}

      <AreaManager
        areas={areas}
        onCreate={createArea}
        onRename={renameArea}
        onDelete={async (id) => {
          await deleteArea(id);
          // Its projects are now unassigned
          refetch();
        }}
        onMove={moveArea}
      />

      {active.length === 0 && !showCreate && (
        <div className="empty-state">
          <div className="empty-state__title">No active projects</div>
          <p>Create one to get started.</p>
        </div>
      )}

      {active.map((project) => (
        <ProjectListItem
          key={project.id}
          project={project}
          areas={areas}
          onClick={() => navigate(`/projects/${project.id}`)}
        />
      ))}

      {completed.length > 0 && (
        <>
          <button
            className="btn btn--ghost section-toggle"
            onClick={() => setShowCompleted(!showCompleted)}
          >
            {showCompleted ? "▾" : "▸"} Completed ({completed.length})
          </button>
          {showCompleted &&
            completed.map((project) => (
              <ProjectListItem
                key={project.id}
                project={project}
                areas={areas}
                onClick={() => navigate(`/projects/${project.id}`)}
              />
            ))}
        </>
      )}
    </div>
  );
}

function ProjectListItem({
  project,
  areas,
  onClick,
}: {
  project: Project;
  areas: Area[];
  onClick: () => void;
}) {
  const area = areas.find((a) => a.id === project.area_id);
  return (
    <button className="card project-list-item" onClick={onClick}>
      <div className="project-list-item__name">{project.name}</div>
      {project.description && (
        <div className="project-list-item__desc">{project.description}</div>
      )}
      <div className="project-list-item__meta">
        <span
          className={`status-badge status-badge--${project.status}`}
        >
          {project.status}
        </span>
        {area && <AreaBadge name={area.name} />}
      </div>
    </button>
  );
}
