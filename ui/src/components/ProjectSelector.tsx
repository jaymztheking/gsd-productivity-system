import { useState } from "react";
import type { Project } from "../types/models";

interface ProjectSelectorProps {
  projects: Project[];
  selected: string | null;
  onSelect: (projectId: string | null) => void;
  onCreateNew: (name: string, indexNotes?: string) => Promise<Project>;
}

export default function ProjectSelector({
  projects,
  selected,
  onSelect,
  onCreateNew,
}: ProjectSelectorProps) {
  const [showNew, setShowNew] = useState(false);
  const [newName, setNewName] = useState("");
  const [newNotes, setNewNotes] = useState("");

  const handleCreate = async () => {
    if (!newName.trim()) return;
    const project = await onCreateNew(newName.trim(), newNotes.trim() || undefined);
    onSelect(project.id);
    setShowNew(false);
    setNewName("");
    setNewNotes("");
  };

  return (
    <div className="project-selector">
      <label className="project-selector__label">Project</label>
      <select
        className="project-selector__select"
        value={selected ?? ""}
        onChange={(e) => {
          const val = e.target.value;
          if (val === "__new__") {
            setShowNew(true);
          } else {
            onSelect(val || null);
          }
        }}
      >
        <option value="">None</option>
        {projects
          .filter((p) => p.status === "active")
          .map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        <option value="__new__">+ New Project...</option>
      </select>

      {showNew && (
        <div className="project-selector__new">
          <input
            type="text"
            placeholder="Project name"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            className="input"
            autoFocus
          />
          <textarea
            placeholder="Index notes (optional)"
            value={newNotes}
            onChange={(e) => setNewNotes(e.target.value)}
            className="textarea"
            rows={3}
          />
          <div className="project-selector__new-actions">
            <button
              type="button"
              className="btn btn--primary btn--sm"
              onClick={handleCreate}
              disabled={!newName.trim()}
            >
              Create
            </button>
            <button
              type="button"
              className="btn btn--ghost btn--sm"
              onClick={() => {
                setShowNew(false);
                setNewName("");
                setNewNotes("");
              }}
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
