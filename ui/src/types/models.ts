export type ActionStatus = "inbox" | "active" | "pending" | "complete";
export type ProjectStatus = "active" | "complete";
export type TagCategory = "context" | "time" | "energy";

export interface Tag {
  id: string;
  name: string;
  category: TagCategory;
}

export interface Project {
  id: string;
  name: string;
  status: ProjectStatus;
  index_notes: string | null;
  created_at: string;
  updated_at: string;
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
}
