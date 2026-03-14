import { updateNextAction } from "../api/client";
import type { NextAction } from "../types/models";

interface ProjectTaskListProps {
  tasks: NextAction[];
  onMove: (index: number, direction: "up" | "down") => Promise<void>;
  onRefetch: () => void;
}

export default function ProjectTaskList({
  tasks,
  onMove,
  onRefetch,
}: ProjectTaskListProps) {
  const handleComplete = async (task: NextAction) => {
    await updateNextAction(task.id, { status: "complete" });
    onRefetch();
  };

  if (tasks.length === 0) {
    return (
      <div className="text-muted" style={{ fontSize: "0.85rem" }}>
        No tasks linked to this project.
      </div>
    );
  }

  return (
    <div className="stack stack--xs">
      {tasks.map((task, idx) => (
        <div
          key={task.id}
          className={`task-order-row ${
            task.status === "complete" ? "task-order-row--complete" : ""
          }`}
        >
          <div className="task-order-row__arrows">
            <button
              className="order-btn"
              disabled={idx === 0}
              onClick={() => onMove(idx, "up")}
              aria-label="Move up"
            >
              ▲
            </button>
            <button
              className="order-btn"
              disabled={idx === tasks.length - 1}
              onClick={() => onMove(idx, "down")}
              aria-label="Move down"
            >
              ▼
            </button>
          </div>
          <div className="task-order-row__content">
            <div className="task-order-row__title">{task.title}</div>
            {task.tags.length > 0 && (
              <div className="task-order-row__tags">
                {task.tags.map((tag) => (
                  <span key={tag.id} className={`tag-badge tag-badge--${tag.category}`}>
                    {tag.name}
                  </span>
                ))}
              </div>
            )}
          </div>
          {task.status !== "complete" && (
            <button
              className="complete-btn"
              onClick={() => handleComplete(task)}
              aria-label="Complete task"
            >
              ○
            </button>
          )}
          {task.status === "complete" && (
            <span className="complete-check">✓</span>
          )}
        </div>
      ))}
    </div>
  );
}
