import type { Tag } from "../types/models";

interface TagBadgeProps {
  tag: Tag;
}

const categoryColors: Record<string, string> = {
  context: "var(--color-context)",
  time: "var(--color-time)",
  energy: "var(--color-energy)",
};

export default function TagBadge({ tag }: TagBadgeProps) {
  return (
    <span
      className="tag-badge"
      style={
        {
          "--badge-color": categoryColors[tag.category] ?? "#888",
        } as React.CSSProperties
      }
    >
      {tag.name}
    </span>
  );
}
