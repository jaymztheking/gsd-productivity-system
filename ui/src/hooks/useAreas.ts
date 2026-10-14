import { useCallback, useEffect, useState } from "react";
import {
  createArea as apiCreate,
  deleteArea as apiDelete,
  fetchAreas,
  reorderAreas as apiReorder,
  updateArea as apiUpdate,
} from "../api/client";
import type { Area } from "../types/models";

export function useAreas() {
  const [areas, setAreas] = useState<Area[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      setAreas(await fetchAreas());
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const createArea = async (name: string) => {
    const area = await apiCreate(name);
    setAreas((prev) => [...prev, area]);
    return area;
  };

  const renameArea = async (id: string, name: string) => {
    const updated = await apiUpdate(id, name);
    setAreas((prev) => prev.map((a) => (a.id === id ? updated : a)));
  };

  const deleteArea = async (id: string) => {
    await apiDelete(id);
    setAreas((prev) => prev.filter((a) => a.id !== id));
  };

  const moveArea = async (index: number, direction: "up" | "down") => {
    const target = direction === "up" ? index - 1 : index + 1;
    if (target < 0 || target >= areas.length) return;
    const reordered = [...areas];
    [reordered[index], reordered[target]] = [reordered[target], reordered[index]];
    setAreas(reordered);
    try {
      await apiReorder(reordered.map((a) => a.id));
    } catch {
      load();
    }
  };

  return { areas, loading, createArea, renameArea, deleteArea, moveArea };
}
