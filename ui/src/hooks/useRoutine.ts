import { useCallback, useEffect, useState } from "react";
import {
  ApiError,
  createRoutineItem,
  deleteRoutineItem,
  fetchRoutineItems,
  fetchRoutineToday,
  reorderRoutineItems,
  setRoutineCompletion,
  updateRoutineItem,
} from "../api/client";
import type { RoutineItem, RoutineToday, Weekday } from "../types/models";

// setTimeout overflows above ~24.8 days; a reset is never that far off, but
// clamp anyway so a bad value cannot fire immediately in a loop.
const MAX_TIMEOUT_MS = 2 ** 31 - 1;

/**
 * Today's checklist plus the full item list for editing.
 *
 * The server decides what "today" is, so the daily reset needs no client
 * logic beyond refetching: at the next_reset_at the server reported, when
 * the tab becomes visible again (timers stall on sleeping phones and
 * background tabs), and when a tick is refused because the day changed.
 */
export function useRoutine() {
  const [today, setToday] = useState<RoutineToday | null>(null);
  const [items, setItems] = useState<RoutineItem[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      const [t, all] = await Promise.all([
        fetchRoutineToday(),
        fetchRoutineItems(),
      ]);
      setToday(t);
      setItems(all);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  // Refetch when the day rolls over
  const resetAt = today?.next_reset_at;
  useEffect(() => {
    if (!resetAt) return;
    const delay = new Date(resetAt).getTime() - Date.now() + 1000;
    const timer = setTimeout(load, Math.min(Math.max(delay, 0), MAX_TIMEOUT_MS));
    return () => clearTimeout(timer);
  }, [resetAt, load]);

  useEffect(() => {
    const onVisible = () => {
      if (document.visibilityState === "visible") load();
    };
    document.addEventListener("visibilitychange", onVisible);
    return () => document.removeEventListener("visibilitychange", onVisible);
  }, [load]);

  const setCompleted = async (id: string, completed: boolean) => {
    if (!today) return;
    const apply = (value: boolean) =>
      setToday((prev) =>
        prev && {
          ...prev,
          items: prev.items.map((i) =>
            i.id === id ? { ...i, completed: value } : i
          ),
        }
      );

    apply(completed);
    try {
      await setRoutineCompletion(id, today.date, completed);
    } catch (err) {
      apply(!completed);
      // 409: the day changed under an open page. Show the new day instead.
      if (err instanceof ApiError && err.status === 409) await load();
      else throw err;
    }
  };

  const createItem = async (title: string, weekdays: Weekday[]) => {
    await createRoutineItem({ title, weekdays });
    await load();
  };

  const updateItem = async (
    id: string,
    data: { title?: string; weekdays?: Weekday[] }
  ) => {
    await updateRoutineItem(id, data);
    await load();
  };

  const deleteItem = async (id: string) => {
    await deleteRoutineItem(id);
    await load();
  };

  /** Reorder a visible subset (e.g. one weekday); others keep their slots. */
  const reorder = async (orderedIds: string[]) => {
    await reorderRoutineItems(orderedIds);
    await load();
  };

  return {
    today,
    items,
    loading,
    refetch: load,
    setCompleted,
    createItem,
    updateItem,
    deleteItem,
    reorder,
  };
}
