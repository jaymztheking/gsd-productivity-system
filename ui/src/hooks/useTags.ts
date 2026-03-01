import { useCallback, useEffect, useState } from "react";
import { fetchTags } from "../api/client";
import type { Tag, TagCategory } from "../types/models";

export function useTags() {
  const [tags, setTags] = useState<Tag[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      const data = await fetchTags();
      setTags(data);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const tagsByCategory: Record<TagCategory, Tag[]> = {
    context: tags.filter((t) => t.category === "context"),
    time: tags.filter((t) => t.category === "time"),
    energy: tags.filter((t) => t.category === "energy"),
  };

  return { tags, tagsByCategory, loading };
}
