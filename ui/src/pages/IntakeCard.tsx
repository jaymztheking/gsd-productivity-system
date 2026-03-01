import { useState } from "react";
import ProjectSelector from "../components/ProjectSelector";
import TagSelector from "../components/TagSelector";
import type { NextAction, Project, Tag, TagCategory } from "../types/models";

interface IntakeCardProps {
  action: NextAction;
  tagsByCategory: Record<TagCategory, Tag[]>;
  projects: Project[];
  onIgnore: (id: string) => void;
  onMakeTask: (
    id: string,
    data: {
      title: string;
      notes: string | null;
      tag_ids: string[];
      project_id: string | null;
    }
  ) => void;
  onMakeProject: (
    name: string,
    description?: string
  ) => Promise<Project>;
}

type Mode = "idle" | "task" | "project";

export default function IntakeCard({
  action,
  tagsByCategory,
  projects,
  onIgnore,
  onMakeTask,
  onMakeProject,
}: IntakeCardProps) {
  const [mode, setMode] = useState<Mode>("idle");
  const [title, setTitle] = useState(action.title);
  const [notes, setNotes] = useState(action.notes ?? "");
  const [selectedTags, setSelectedTags] = useState<
    Record<TagCategory, string | null>
  >({
    context: null,
    time: null,
    energy: null,
  });
  const [projectId, setProjectId] = useState<string | null>(null);
  const [projectName, setProjectName] = useState(action.title);
  const [projectNotes, setProjectNotes] = useState("");

  const handleTagSelect = (category: TagCategory, tagId: string | null) => {
    setSelectedTags((prev) => ({ ...prev, [category]: tagId }));
  };

  const handleSaveTask = () => {
    const tag_ids = Object.values(selectedTags).filter(Boolean) as string[];
    onMakeTask(action.id, {
      title: title.trim(),
      notes: notes.trim() || null,
      tag_ids,
      project_id: projectId,
    });
  };

  const handleSaveProject = async () => {
    if (!projectName.trim()) return;
    await onMakeProject(projectName.trim(), projectNotes.trim() || undefined);
  };

  return (
    <div className="card stack stack--md">
      <div>
        <h3 style={{ fontSize: "1.1rem", fontWeight: 600 }}>{action.title}</h3>
        {action.notes && (
          <p
            style={{
              fontSize: "0.85rem",
              color: "var(--color-text-muted)",
              marginTop: "0.25rem",
            }}
          >
            {action.notes}
          </p>
        )}
      </div>

      {mode === "idle" && (
        <div className="intake-actions">
          <button
            className="btn btn--danger"
            onClick={() => onIgnore(action.id)}
          >
            Ignore
          </button>
          <button
            className="btn btn--primary"
            onClick={() => setMode("task")}
            style={{ flex: 1 }}
          >
            Make Task
          </button>
          <button
            className="btn btn--success"
            onClick={() => setMode("project")}
          >
            Make Project
          </button>
        </div>
      )}

      {mode === "task" && (
        <div className="intake-form">
          <input
            type="text"
            className="input"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Next action (concrete, physical)"
          />
          <textarea
            className="textarea"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Notes, URLs, context..."
            rows={3}
          />
          <TagSelector
            label="Context"
            category="context"
            tags={tagsByCategory.context}
            selected={selectedTags.context}
            onSelect={(id) => handleTagSelect("context", id)}
          />
          <TagSelector
            label="Time Horizon"
            category="time"
            tags={tagsByCategory.time}
            selected={selectedTags.time}
            onSelect={(id) => handleTagSelect("time", id)}
          />
          <TagSelector
            label="Energy"
            category="energy"
            tags={tagsByCategory.energy}
            selected={selectedTags.energy}
            onSelect={(id) => handleTagSelect("energy", id)}
          />
          <ProjectSelector
            projects={projects}
            selected={projectId}
            onSelect={setProjectId}
            onCreateNew={async (name, description) => {
              const p = await onMakeProject(name, description);
              return p;
            }}
          />
          <div className="intake-actions">
            <button
              className="btn btn--ghost"
              onClick={() => setMode("idle")}
            >
              Back
            </button>
            <button
              className="btn btn--primary"
              onClick={handleSaveTask}
              disabled={!title.trim()}
              style={{ flex: 1 }}
            >
              Save as Task
            </button>
          </div>
        </div>
      )}

      {mode === "project" && (
        <div className="intake-form">
          <input
            type="text"
            className="input"
            value={projectName}
            onChange={(e) => setProjectName(e.target.value)}
            placeholder="Project name"
          />
          <textarea
            className="textarea"
            value={projectNotes}
            onChange={(e) => setProjectNotes(e.target.value)}
            placeholder="Description — what is this project about?"
            rows={4}
          />
          <div className="intake-actions">
            <button
              className="btn btn--ghost"
              onClick={() => setMode("idle")}
            >
              Back
            </button>
            <button
              className="btn btn--success"
              onClick={handleSaveProject}
              disabled={!projectName.trim()}
              style={{ flex: 1 }}
            >
              Create Project
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
