import { useCallback, useEffect, useState } from "react";
import {
  fetchNextActions,
  updateNextAction,
} from "../api/client";
import { useProjects } from "../hooks/useProjects";
import { useTags } from "../hooks/useTags";
import type { NextAction, Project, TagCategory } from "../types/models";
import FilterPanel from "./FilterPanel";
import TaskCard from "./TaskCard";

export default function EngagePage() {
  const { tagsByCategory, loading: tagsLoading } = useTags();
  const { projects, createProject } = useProjects();

  const [selectedTags, setSelectedTags] = useState<
    Record<TagCategory, string | null>
  >({
    context: null,
    time: null,
    energy: null,
  });
  const [showPending, setShowPending] = useState(false);
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
        // Active first, then pending
        setActions([...activeItems, ...pendingItems]);
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
    setActions((prev) => prev.map((a) => (a.id === id ? updated : a)));
  };

  const handleCreateProject = async (
    name: string,
    indexNotes?: string
  ): Promise<Project> => {
    return createProject(name, indexNotes);
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
      ) : (
        <div className="stack stack--sm">
          {actions.map((action) => (
            <TaskCard
              key={action.id}
              action={action}
              tagsByCategory={tagsByCategory}
              projects={projects}
              onComplete={handleComplete}
              onUpdate={handleUpdate}
              onCreateProject={handleCreateProject}
            />
          ))}
        </div>
      )}
    </div>
  );
}
