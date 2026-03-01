import { useState } from "react";
import TagBadge from "../components/TagBadge";
import TagSelector from "../components/TagSelector";
import ProjectSelector from "../components/ProjectSelector";
import type { NextAction, Project, Tag, TagCategory } from "../types/models";

interface TaskCardProps {
  action: NextAction;
  tagsByCategory: Record<TagCategory, Tag[]>;
  projects: Project[];
  onComplete: (id: string) => void;
  onUpdate: (
    id: string,
    data: {
      title?: string;
      notes?: string | null;
      status?: "active" | "pending";
      tag_ids?: string[];
      project_id?: string | null;
    }
  ) => void;
  onCreateProject: (name: string, indexNotes?: string) => Promise<Project>;
}

export default function TaskCard({
  action,
  tagsByCategory,
  projects,
  onComplete,
  onUpdate,
  onCreateProject,
}: TaskCardProps) {
  const [expanded, setExpanded] = useState(false);
  const [title, setTitle] = useState(action.title);
  const [notes, setNotes] = useState(action.notes ?? "");
  const [selectedTags, setSelectedTags] = useState<
    Record<TagCategory, string | null>
  >(() => {
    const map: Record<TagCategory, string | null> = {
      context: null,
      time: null,
      energy: null,
    };
    action.tags.forEach((t) => {
      map[t.category] = t.id;
    });
    return map;
  });
  const [projectId, setProjectId] = useState(action.project_id);
  const [status, setStatus] = useState(action.status as "active" | "pending");
  const [exiting, setExiting] = useState(false);

  const handleComplete = () => {
    setExiting(true);
    setTimeout(() => onComplete(action.id), 250);
  };

  const handleSave = () => {
    const tag_ids = Object.values(selectedTags).filter(Boolean) as string[];
    onUpdate(action.id, {
      title: title.trim(),
      notes: notes.trim() || null,
      status,
      tag_ids,
      project_id: projectId,
    });
    setExpanded(false);
  };

  const isPending = action.status === "pending";

  return (
    <div
      className={`card stack stack--sm ${isPending ? "card--pending" : ""} ${exiting ? "card--exiting" : ""}`}
    >
      {/* Collapsed view */}
      <div
        className="row row--between gap-md"
        onClick={() => setExpanded(!expanded)}
        style={{ cursor: "pointer" }}
      >
        <div style={{ flex: 1, minWidth: 0 }}>
          <div className="row gap-sm" style={{ flexWrap: "wrap" }}>
            <span style={{ fontWeight: 600, fontSize: "0.95rem" }}>
              {action.title}
            </span>
            {isPending && (
              <span
                className="tag-badge"
                style={
                  {
                    "--badge-color": "var(--color-pending)",
                  } as React.CSSProperties
                }
              >
                Pending
              </span>
            )}
          </div>
          <div
            className="row gap-sm"
            style={{ flexWrap: "wrap", marginTop: "0.25rem" }}
          >
            {action.tags.map((t) => (
              <TagBadge key={t.id} tag={t} />
            ))}
            {action.project && (
              <span
                style={{
                  fontSize: "0.75rem",
                  color: "var(--color-text-muted)",
                }}
              >
                {action.project.name}
              </span>
            )}
          </div>
          {action.notes && !expanded && (
            <p
              style={{
                fontSize: "0.8rem",
                color: "var(--color-text-muted)",
                marginTop: "0.25rem",
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
              }}
            >
              {action.notes}
            </p>
          )}
        </div>
        <button
          className="complete-btn"
          onClick={(e) => {
            e.stopPropagation();
            handleComplete();
          }}
          title="Mark complete"
        />
      </div>

      {/* Expanded edit view */}
      {expanded && (
        <div className="intake-form" onClick={(e) => e.stopPropagation()}>
          <input
            type="text"
            className="input"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
          <textarea
            className="textarea"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Notes..."
            rows={3}
          />
          <TagSelector
            label="Context"
            category="context"
            tags={tagsByCategory.context}
            selected={selectedTags.context}
            onSelect={(id) =>
              setSelectedTags((prev) => ({ ...prev, context: id }))
            }
          />
          <TagSelector
            label="Time Horizon"
            category="time"
            tags={tagsByCategory.time}
            selected={selectedTags.time}
            onSelect={(id) =>
              setSelectedTags((prev) => ({ ...prev, time: id }))
            }
          />
          <TagSelector
            label="Energy"
            category="energy"
            tags={tagsByCategory.energy}
            selected={selectedTags.energy}
            onSelect={(id) =>
              setSelectedTags((prev) => ({ ...prev, energy: id }))
            }
          />
          <ProjectSelector
            projects={projects}
            selected={projectId}
            onSelect={setProjectId}
            onCreateNew={onCreateProject}
          />
          <div className="row gap-sm">
            <label
              style={{
                fontSize: "0.8rem",
                fontWeight: 600,
                color: "var(--color-text-muted)",
                textTransform: "uppercase",
              }}
            >
              Status
            </label>
            <select
              className="project-selector__select"
              value={status}
              onChange={(e) =>
                setStatus(e.target.value as "active" | "pending")
              }
              style={{ width: "auto", flex: 1 }}
            >
              <option value="active">Active</option>
              <option value="pending">Pending</option>
            </select>
          </div>
          <div className="intake-actions">
            <button
              className="btn btn--ghost"
              onClick={() => setExpanded(false)}
            >
              Cancel
            </button>
            <button
              className="btn btn--primary"
              onClick={handleSave}
              disabled={!title.trim()}
              style={{ flex: 1 }}
            >
              Save
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
