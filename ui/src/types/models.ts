export type ActionStatus = "inbox" | "active" | "pending" | "complete";
export type ProjectStatus = "active" | "complete";
export type TagCategory = "context" | "time" | "energy";

export interface Tag {
  id: string;
  name: string;
  category: TagCategory;
  sort_order: number;
}

export interface ProjectLink {
  id: string;
  project_id: string;
  url: string;
  label: string;
  sort_order: number;
  created_at: string;
}

export interface Project {
  id: string;
  name: string;
  status: ProjectStatus;
  description: string | null;
  parent_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProjectDetail extends Project {
  links: ProjectLink[];
  children: Project[];
}

export interface NextAction {
  id: string;
  title: string;
  notes: string | null;
  status: ActionStatus;
  project_id: string | null;
  tags: Tag[];
  project: Project | null;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
  deleted_at: string | null;
  project_sort_order: number;
}
