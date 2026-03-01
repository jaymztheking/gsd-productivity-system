import { useCallback, useEffect, useState } from "react";
import {
  createProject as apiCreateProject,
  deleteProject as apiDeleteProject,
  updateProject as apiUpdateProject,
  fetchProjects,
} from "../api/client";
import type { Project, ProjectStatus } from "../types/models";

export function useProjects() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      const data = await fetchProjects();
      setProjects(data);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const createProject = async (
    name: string,
    opts?: {
      description?: string;
      parentId?: string;
    }
  ) => {
    const project = await apiCreateProject({
      name,
      description: opts?.description || null,
      parent_id: opts?.parentId || null,
    });
    setProjects((prev) => [project, ...prev]);
    return project;
  };

  const updateProject = async (
    id: string,
    data: {
      name?: string;
      status?: ProjectStatus;
      description?: string | null;
    }
  ) => {
    const updated = await apiUpdateProject(id, data);
    setProjects((prev) =>
      prev.map((p) => (p.id === id ? updated : p))
    );
    return updated;
  };

  const deleteProjectFromList = async (id: string) => {
    await apiDeleteProject(id);
    setProjects((prev) => prev.filter((p) => p.id !== id));
  };

  return {
    projects,
    loading,
    refetch: load,
    createProject,
    updateProject,
    deleteProject: deleteProjectFromList,
  };
}
