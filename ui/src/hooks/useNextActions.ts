import { useCallback, useEffect, useState } from "react";
import {
  createNextAction as apiCreate,
  deleteNextAction as apiDelete,
  fetchNextActions,
  updateNextAction as apiUpdate,
} from "../api/client";
import type { ActionStatus, NextAction } from "../types/models";

interface UseNextActionsParams {
  status?: ActionStatus;
  tag_ids?: string[];
}

export function useNextActions(params?: UseNextActionsParams) {
  const [actions, setActions] = useState<NextAction[]>([]);
  const [loading, setLoading] = useState(true);

  // Stable key for deps
  const paramKey = JSON.stringify(params ?? {});

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchNextActions(params);
      setActions(data);
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [paramKey]);

  useEffect(() => {
    load();
  }, [load]);

  const createAction = async (data: Parameters<typeof apiCreate>[0]) => {
    const action = await apiCreate(data);
    // Refetch to get correct ordering
    await load();
    return action;
  };

  const updateAction = async (
    id: string,
    data: Parameters<typeof apiUpdate>[1]
  ) => {
    const updated = await apiUpdate(id, data);
    setActions((prev) =>
      prev.map((a) => (a.id === id ? updated : a))
    );
    return updated;
  };

  const deleteAction = async (id: string) => {
    await apiDelete(id);
    setActions((prev) => prev.filter((a) => a.id !== id));
  };

  const removeFromList = (id: string) => {
    setActions((prev) => prev.filter((a) => a.id !== id));
  };

  return {
    actions,
    loading,
    refetch: load,
    createAction,
    updateAction,
    deleteAction,
    removeFromList,
  };
}
