import {
  DndContext,
  KeyboardSensor,
  PointerSensor,
  closestCenter,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import {
  SortableContext,
  arrayMove,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { useCallback, useEffect, useState } from "react";
import {
  fetchNextActions,
  reorderNextActions,
  updateNextAction,
} from "../api/client";
import { useAreas } from "../hooks/useAreas";
import { useProjects } from "../hooks/useProjects";
import { useTags } from "../hooks/useTags";
import type { NextAction, Project, TagCategory } from "../types/models";
import EngageBoard from "./EngageBoard";
import FilterPanel from "./FilterPanel";
import SortableTaskCard from "./SortableTaskCard";

type ViewMode = "list" | "columns";
const VIEW_KEY = "gsd.engage.view";

// Remembered per browser; storage can be unavailable (private mode)
function loadView(): ViewMode {
  try {
    return localStorage.getItem(VIEW_KEY) === "columns" ? "columns" : "list";
  } catch {
    return "list";
  }
}

export default function EngagePage() {
  const { tagsByCategory, loading: tagsLoading } = useTags();
  const { projects, createProject } = useProjects();
  const { areas } = useAreas();

  const [selectedTags, setSelectedTags] = useState<
    Record<TagCategory, string | null>
  >({
    context: null,
    time: null,
    energy: null,
  });
  const [showPending, setShowPending] = useState(false);
  const [view, setView] = useState<ViewMode>(loadView);
  const [actions, setActions] = useState<NextAction[]>([]);
  const [loading, setLoading] = useState(true);

  const activeTagIds = Object.values(selectedTags).filter(
    Boolean
  ) as string[];

  const loadActions = useCallback(async () => {
    setLoading(true);
    try {
      // Fetch active items
      const activePromise = fetchNextActions({
        status: "active",
        tag_ids: activeTagIds.length > 0 ? activeTagIds : undefined,
      });

      if (showPending) {
        // Fetch pending items too and merge
        const pendingPromise = fetchNextActions({
          status: "pending",
          tag_ids: activeTagIds.length > 0 ? activeTagIds : undefined,
        });
        const [activeItems, pendingItems] = await Promise.all([
          activePromise,
          pendingPromise,
        ]);
        // Active and pending share one manual order
        setActions(
          [...activeItems, ...pendingItems].sort(
            (a, b) => a.engage_sort_order - b.engage_sort_order
          )
        );
      } else {
        const activeItems = await activePromise;
        setActions(activeItems);
      }
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(activeTagIds), showPending]);

  useEffect(() => {
    loadActions();
  }, [loadActions]);

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleDragEnd = async ({ active, over }: DragEndEvent) => {
    if (!over || active.id === over.id) return;
    const from = actions.findIndex((a) => a.id === active.id);
    const to = actions.findIndex((a) => a.id === over.id);
    const reordered = arrayMove(actions, from, to);
    setActions(reordered);
    try {
      // Only the shown tasks are sent; ones hidden by filters keep their places
      await reorderNextActions(reordered.map((a) => a.id));
    } catch {
      loadActions();
    }
  };

  const changeView = (next: ViewMode) => {
    setView(next);
    try {
      localStorage.setItem(VIEW_KEY, next);
    } catch {
      // Not remembered; the choice still applies until reload
    }
  };

  const handleBoardDrop = async (
    taskId: string,
    newAreaId: string | null | undefined,
    columnOrder: string[]
  ) => {
    try {
      if (newAreaId !== undefined) {
        await updateNextAction(taskId, { area_id: newAreaId });
      }
      await reorderNextActions(columnOrder);
    } catch {
      loadActions();
    }
  };

  const handleTagToggle = (category: TagCategory, tagId: string | null) => {
    setSelectedTags((prev) => ({ ...prev, [category]: tagId }));
  };

  const handleComplete = async (id: string) => {
    // Optimistic removal
    setActions((prev) => prev.filter((a) => a.id !== id));
    try {
      await updateNextAction(id, { status: "complete" });
    } catch {
      // Rollback on failure
      loadActions();
    }
  };

  const handleUpdate = async (
    id: string,
    data: Parameters<typeof updateNextAction>[1]
  ) => {
    const updated = await updateNextAction(id, data);
    setActions((prev) =>
      updated.status === "someday"
        ? prev.filter((a) => a.id !== id)
        : prev.map((a) => (a.id === id ? updated : a))
    );
  };

  const handleCreateProject = async (
    name: string,
    description?: string
  ): Promise<Project> => {
    return createProject(name, { description });
  };

  if (tagsLoading) {
    return <div className="loading">Loading...</div>;
  }

  return (
    <div className="stack stack--lg">
      <FilterPanel
        tagsByCategory={tagsByCategory}
        selectedTags={selectedTags}
        showPending={showPending}
        onTagToggle={handleTagToggle}
        onPendingToggle={() => setShowPending((prev) => !prev)}
      />

      <div className="view-switch" role="radiogroup" aria-label="Engage view">
        {(["list", "columns"] as const).map((mode) => (
          <button
            key={mode}
            role="radio"
            aria-checked={view === mode}
            className={`day-chip ${view === mode ? "day-chip--on" : ""}`}
            onClick={() => changeView(mode)}
          >
            {mode === "list" ? "List" : "Columns by area"}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="loading">Loading tasks...</div>
      ) : actions.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state__icon">&#127919;</div>
          <div className="empty-state__title">No matching tasks</div>
          <p>
            {activeTagIds.length > 0
              ? "Try adjusting your filters."
              : "Create some tasks to get started."}
          </p>
        </div>
      ) : view === "columns" ? (
        <EngageBoard
          actions={actions}
          areas={areas}
          onActionsChange={setActions}
          onDrop={handleBoardDrop}
          tagsByCategory={tagsByCategory}
          projects={projects}
          onComplete={handleComplete}
          onUpdate={handleUpdate}
          onCreateProject={handleCreateProject}
        />
      ) : (
        <DndContext
          sensors={sensors}
          collisionDetection={closestCenter}
          onDragEnd={handleDragEnd}
        >
          <SortableContext
            items={actions.map((a) => a.id)}
            strategy={verticalListSortingStrategy}
          >
            <div className="stack stack--sm">
              {actions.map((action) => (
                <SortableTaskCard
                  key={action.id}
                  action={action}
                  tagsByCategory={tagsByCategory}
                  projects={projects}
                  areas={areas}
                  onComplete={handleComplete}
                  onUpdate={handleUpdate}
                  onCreateProject={handleCreateProject}
                />
              ))}
            </div>
          </SortableContext>
        </DndContext>
      )}
    </div>
  );
}
