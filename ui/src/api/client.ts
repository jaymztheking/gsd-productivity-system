import type {
  ActionStatus,
  NextAction,
  Project,
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

export function fetchProjects(): Promise<Project[]> {
  return request("/projects");
}

export function createProject(data: {
  name: string;
  index_notes?: string | null;
}): Promise<Project> {
  return request("/projects", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function updateProject(
  id: string,
  data: { name?: string; status?: ProjectStatus; index_notes?: string | null }
): Promise<Project> {
  return request(`/projects/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

// --- Next Actions ---

export function fetchNextActions(params?: {
  status?: ActionStatus;
  tag_ids?: string[];
}): Promise<NextAction[]> {
  const url = new URL(`${BASE}/next-actions`, window.location.origin);
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
