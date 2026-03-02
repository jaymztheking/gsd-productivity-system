import { useCallback, useEffect, useState } from "react";
import {
  fetchProject,
  fetchProjectTasks,
  fetchProjectHistory,
  updateProject as apiUpdateProject,
  deleteProject as apiDeleteProject,
  createProjectLink as apiCreateLink,
  updateProjectLink as apiUpdateLink,
  deleteProjectLink as apiDeleteLink,
  reorderProjectTasks as apiReorderTasks,
} from "../api/client";
import type {
  NextAction,
  ProjectDetail,
  ProjectStatus,
} from "../types/models";

export function useProjectDetail(projectId: string) {
  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [tasks, setTasks] = useState<NextAction[]>([]);
  const [history, setHistory] = useState<NextAction[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [proj, taskList, historyList] = await Promise.all([
        fetchProject(projectId),
        fetchProjectTasks(projectId),
        fetchProjectHistory(projectId),
      ]);
      setProject(proj);
      setTasks(taskList);
      setHistory(historyList);
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    load();
  }, [load]);

  // --- Project ---

  const updateProject = async (data: {
    name?: string;
    status?: ProjectStatus;
    description?: string | null;
  }) => {
    if (!project) return;
    const updated = await apiUpdateProject(project.id, data);
    setProject((prev) => (prev ? { ...prev, ...updated } : prev));
  };

  const deleteProjectAction = async () => {
    if (!project) return;
    await apiDeleteProject(project.id);
  };

  // --- Links ---

  const addLink = async (url: string, label: string) => {
    if (!project) return;
    const link = await apiCreateLink(project.id, { url, label });
    setProject((prev) =>
      prev ? { ...prev, links: [...prev.links, link] } : prev
    );
  };

  const editLink = async (
    linkId: string,
    data: { url?: string; label?: string }
  ) => {
    if (!project) return;
    const updated = await apiUpdateLink(project.id, linkId, data);
    setProject((prev) =>
      prev
        ? {
            ...prev,
            links: prev.links.map((l) => (l.id === linkId ? updated : l)),
          }
        : prev
    );
  };

  const removeLink = async (linkId: string) => {
    if (!project) return;
    await apiDeleteLink(project.id, linkId);
    setProject((prev) =>
      prev
        ? { ...prev, links: prev.links.filter((l) => l.id !== linkId) }
        : prev
    );
  };

  // --- Task Reordering ---

  const moveTask = async (index: number, direction: "up" | "down") => {
    const newIndex = direction === "up" ? index - 1 : index + 1;
    if (newIndex < 0 || newIndex >= tasks.length) return;

    const reordered = [...tasks];
    [reordered[index], reordered[newIndex]] = [
      reordered[newIndex],
      reordered[index],
    ];
    setTasks(reordered);

    // Persist to server
    await apiReorderTasks(
      projectId,
      reordered.map((t) => t.id)
    );
  };

  return {
    project,
    tasks,
    history,
    loading,
    refetch: load,
    updateProject,
    deleteProject: deleteProjectAction,
    addLink,
    editLink,
    removeLink,
    moveTask,
  };
}
