import { useState } from "react";
import {
  createNextAction,
  updateNextAction,
  deleteNextAction,
} from "../api/client";
import { useNextActions } from "../hooks/useNextActions";
import { useProjects } from "../hooks/useProjects";
import { useTags } from "../hooks/useTags";
import type { Project } from "../types/models";
import IntakeCard from "./IntakeCard";

export default function IntakePage() {
  const { actions, loading, removeFromList, refetch } = useNextActions({
    status: "inbox",
  });
  const { tagsByCategory } = useTags();
  const { projects, createProject } = useProjects();

  const [captureText, setCaptureText] = useState("");
  const [capturing, setCapturing] = useState(false);

  const handleCapture = async () => {
    if (!captureText.trim()) return;
    setCapturing(true);
    try {
      await createNextAction({
        title: captureText.trim(),
        status: "inbox",
      });
      setCaptureText("");
      refetch();
    } finally {
      setCapturing(false);
    }
  };

  const handleIgnore = async (id: string) => {
    await deleteNextAction(id);
    removeFromList(id);
  };

  const handleMakeTask = async (
    id: string,
    data: {
      title: string;
      notes: string | null;
      tag_ids: string[];
      project_id: string | null;
    }
  ) => {
    await updateNextAction(id, {
      ...data,
      status: "active",
    });
    removeFromList(id);
  };

  const handleMakeProject = async (
    actionId: string,
    name: string,
    description?: string
  ): Promise<Project> => {
    const project = await createProject(name, {
      description: description || undefined,
    });
    // Delete the inbox item after creating the project
    await deleteNextAction(actionId);
    removeFromList(actionId);
    return project;
  };

  if (loading) {
    return <div className="loading">Loading inbox...</div>;
  }

  return (
    <div className="stack stack--md">
      {/* Capture form */}
      <div className="capture-form">
        <input
          className="input"
          placeholder="Capture a thought..."
          value={captureText}
          onChange={(e) => setCaptureText(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleCapture()}
          disabled={capturing}
        />
        <button
          className="btn btn--primary"
          onClick={handleCapture}
          disabled={!captureText.trim() || capturing}
        >
          + Capture
        </button>
      </div>

      {actions.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state__icon">&#10003;</div>
          <div className="empty-state__title">Inbox Zero</div>
          <p>Nothing to process. Go get things done.</p>
        </div>
      ) : (
        <>
          <div className="inbox-counter">
            {actions.length} item{actions.length !== 1 ? "s" : ""} in inbox
          </div>
          <IntakeCard
            key={actions[0].id}
            action={actions[0]}
            tagsByCategory={tagsByCategory}
            projects={projects}
            onIgnore={handleIgnore}
            onMakeTask={handleMakeTask}
            onMakeProject={(name, description) =>
              handleMakeProject(actions[0].id, name, description)
            }
          />
          {actions.length > 1 && (
            <div
              style={{
                fontSize: "0.8rem",
                color: "var(--color-text-muted)",
                textAlign: "center",
              }}
            >
              {actions.length - 1} more after this
            </div>
          )}
        </>
      )}
    </div>
  );
}
