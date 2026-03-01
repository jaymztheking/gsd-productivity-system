import type {
  ActionStatus,
  NextAction,
  Project,
  ProjectDetail,
  ProjectLink,
  ProjectStatus,
  Tag,
} from "../types/models";

const BASE = "/api";

async function request<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

// --- Tags ---

export function fetchTags(): Promise<Tag[]> {
  return request("/tags");
}

// --- Projects ---

export function fetchProjects(rootOnly = true): Promise<Project[]> {
  return request(`/projects?root_only=${rootOnly}`);
}

export function fetchProject(id: string): Promise<ProjectDetail> {
  return request(`/projects/${id}`);
}

export function createProject(data: {
  name: string;
  description?: string | null;
  parent_id?: string | null;
}): Promise<Project> {
  return request("/projects", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function updateProject(
  id: string,
  data: {
    name?: string;
    status?: ProjectStatus;
    description?: string | null;
    parent_id?: string | null;
  }
): Promise<Project> {
  return request(`/projects/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function deleteProject(id: string): Promise<void> {
  return request(`/projects/${id}`, { method: "DELETE" });
}

// --- Project Tasks ---

export function fetchProjectTasks(projectId: string): Promise<NextAction[]> {
  return request(`/projects/${projectId}/tasks`);
}

export function fetchProjectHistory(projectId: string): Promise<NextAction[]> {
  return request(`/projects/${projectId}/history`);
}

export function reorderProjectTasks(
  projectId: string,
  orderedIds: string[]
): Promise<void> {
  return request(`/projects/${projectId}/tasks/order`, {
    method: "PUT",
    body: JSON.stringify({ ordered_ids: orderedIds }),
  });
}

// --- Project Links ---

export function createProjectLink(
  projectId: string,
  data: { url: string; label: string }
): Promise<ProjectLink> {
  return request(`/projects/${projectId}/links`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function updateProjectLink(
  projectId: string,
  linkId: string,
  data: { url?: string; label?: string }
): Promise<ProjectLink> {
  return request(`/projects/${projectId}/links/${linkId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function deleteProjectLink(
  projectId: string,
  linkId: string
): Promise<void> {
  return request(`/projects/${projectId}/links/${linkId}`, {
    method: "DELETE",
  });
}

export function reorderProjectLinks(
  projectId: string,
  orderedIds: string[]
): Promise<void> {
  return request(`/projects/${projectId}/links/order`, {
    method: "PUT",
    body: JSON.stringify({ ordered_ids: orderedIds }),
  });
}

// --- Next Actions ---

export function fetchNextActions(params?: {
  status?: ActionStatus;
  tag_ids?: string[];
}): Promise<NextAction[]> {
  const url = new URL("/next-actions", window.location.origin);
  if (params?.status) url.searchParams.set("status", params.status);
  if (params?.tag_ids) {
    params.tag_ids.forEach((id) => url.searchParams.append("tag_ids", id));
  }
  return request(url.pathname + url.search);
}

export function createNextAction(data: {
  title: string;
  notes?: string | null;
  status?: ActionStatus;
  project_id?: string | null;
  tag_ids?: string[];
}): Promise<NextAction> {
  return request("/next-actions", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function updateNextAction(
  id: string,
  data: {
    title?: string;
    notes?: string | null;
    status?: ActionStatus;
    project_id?: string | null;
    tag_ids?: string[];
  }
): Promise<NextAction> {
  return request(`/next-actions/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function deleteNextAction(id: string): Promise<void> {
  return request(`/next-actions/${id}`, { method: "DELETE" });
}
