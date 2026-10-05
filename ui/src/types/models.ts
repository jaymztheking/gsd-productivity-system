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

/** 0 = Monday ... 6 = Sunday, matching the API */
export type Weekday = 0 | 1 | 2 | 3 | 4 | 5 | 6;

export interface RoutineItem {
  id: string;
  title: string;
  weekdays: Weekday[];
  sort_order: number;
  created_on: string;
  created_at: string;
  updated_at: string;
}

export interface RoutineTodayItem extends RoutineItem {
  completed: boolean;
}

export interface RoutineToday {
  /** The user's local date (YYYY-MM-DD), decided by the server */
  date: string;
  weekday: Weekday;
  /** UTC instant when today ends locally; refetch then */
  next_reset_at: string;
  items: RoutineTodayItem[];
}
