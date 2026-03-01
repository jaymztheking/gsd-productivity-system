import type { Tag, TagCategory } from "../types/models";

interface TagSelectorProps {
  label: string;
  category: TagCategory;
  tags: Tag[];
  selected: string | null;
  onSelect: (tagId: string | null) => void;
}

const categoryColors: Record<TagCategory, string> = {
  context: "var(--color-context)",
  time: "var(--color-time)",
  energy: "var(--color-energy)",
};

export default function TagSelector({
  label,
  category,
  tags,
  selected,
  onSelect,
}: TagSelectorProps) {
  return (
    <div className="tag-selector">
      <span className="tag-selector__label">{label}</span>
      <div className="tag-selector__buttons">
        {tags.map((tag) => {
          const isSelected = selected === tag.id;
          return (
            <button
              key={tag.id}
              type="button"
              className={`tag-btn ${isSelected ? "tag-btn--selected" : ""}`}
              style={
                {
                  "--btn-color": categoryColors[category],
                } as React.CSSProperties
              }
              onClick={() => onSelect(isSelected ? null : tag.id)}
            >
              {tag.name}
            </button>
          );
        })}
      </div>
    </div>
  );
}
