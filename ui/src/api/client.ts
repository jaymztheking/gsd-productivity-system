import type {
  ActionStatus,
  NextAction,
  Project,
  ProjectDetail,
  ProjectLink,
  ProjectStatus,
  RoutineItem,
  RoutineToday,
  Tag,
  Weekday,
} from "../types/models";

const BASE = "/api";

/** An API error that keeps the HTTP status, so callers can react to it. */
export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

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
    throw new ApiError(res.status, `API ${res.status}: ${text}`);
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

// --- Routine ---

export function fetchRoutineToday(): Promise<RoutineToday> {
  return request("/routine/today");
}

export function fetchRoutineItems(): Promise<RoutineItem[]> {
  return request("/routine/items");
}

export function createRoutineItem(data: {
  title: string;
  weekdays: Weekday[];
}): Promise<RoutineItem> {
  return request("/routine/items", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function updateRoutineItem(
  id: string,
  data: { title?: string; weekdays?: Weekday[] }
): Promise<RoutineItem> {
  return request(`/routine/items/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function deleteRoutineItem(id: string): Promise<void> {
  return request(`/routine/items/${id}`, { method: "DELETE" });
}

export function reorderRoutineItems(orderedIds: string[]): Promise<void> {
  return request("/routine/items/order", {
    method: "PUT",
    body: JSON.stringify({ ordered_ids: orderedIds }),
  });
}

/** Rejects with ApiError 409 if `date` is no longer the server's today. */
export function setRoutineCompletion(
  id: string,
  date: string,
  completed: boolean
): Promise<void> {
  return request(`/routine/items/${id}/completion`, {
    method: "PUT",
    body: JSON.stringify({ date, completed }),
  });
}
