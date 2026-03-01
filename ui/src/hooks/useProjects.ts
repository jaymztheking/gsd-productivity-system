import { useCallback, useEffect, useState } from "react";
import {
  createProject as apiCreateProject,
  fetchProjects,
} from "../api/client";
import type { Project } from "../types/models";

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

  const createProject = async (name: string, indexNotes?: string) => {
    const project = await apiCreateProject({
      name,
      index_notes: indexNotes || null,
    });
    setProjects((prev) => [project, ...prev]);
    return project;
  };

  return { projects, loading, refetch: load, createProject };
}
