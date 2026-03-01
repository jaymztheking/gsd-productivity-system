import { updateNextAction, deleteNextAction } from "../api/client";
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
    indexNotes?: string
  ): Promise<Project> => {
    const project = await createProject(name, indexNotes);
    // Delete the inbox item after creating the project
    await deleteNextAction(actionId);
    removeFromList(actionId);
    return project;
  };

  if (loading) {
    return <div className="loading">Loading inbox...</div>;
  }

  if (actions.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-state__icon">&#10003;</div>
        <div className="empty-state__title">Inbox Zero</div>
        <p>Nothing to process. Go get things done.</p>
      </div>
    );
  }

  const current = actions[0];

  return (
    <div className="stack stack--md">
      <div className="inbox-counter">
        {actions.length} item{actions.length !== 1 ? "s" : ""} in inbox
      </div>
      <IntakeCard
        key={current.id}
        action={current}
        tagsByCategory={tagsByCategory}
        projects={projects}
        onIgnore={handleIgnore}
        onMakeTask={handleMakeTask}
        onMakeProject={(name, indexNotes) =>
          handleMakeProject(current.id, name, indexNotes)
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
    </div>
  );
}
