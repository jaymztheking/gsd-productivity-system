import TagSelector from "../components/TagSelector";
import type { Tag, TagCategory } from "../types/models";

interface FilterPanelProps {
  tagsByCategory: Record<TagCategory, Tag[]>;
  selectedTags: Record<TagCategory, string | null>;
  showPending: boolean;
  onTagToggle: (category: TagCategory, tagId: string | null) => void;
  onPendingToggle: () => void;
}

export default function FilterPanel({
  tagsByCategory,
  selectedTags,
  showPending,
  onTagToggle,
  onPendingToggle,
}: FilterPanelProps) {
  return (
    <div className="stack stack--md">
      <TagSelector
        label="Context"
        category="context"
        tags={tagsByCategory.context}
        selected={selectedTags.context}
        onSelect={(id) => onTagToggle("context", id)}
      />
      <TagSelector
        label="Energy"
        category="energy"
        tags={tagsByCategory.energy}
        selected={selectedTags.energy}
        onSelect={(id) => onTagToggle("energy", id)}
      />
      <TagSelector
        label="Time Horizon"
        category="time"
        tags={tagsByCategory.time}
        selected={selectedTags.time}
        onSelect={(id) => onTagToggle("time", id)}
      />
      <div
        className={`toggle ${showPending ? "toggle--on" : ""}`}
        onClick={onPendingToggle}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") onPendingToggle();
        }}
      >
        <div className="toggle__track">
          <div className="toggle__thumb" />
        </div>
        <span className="toggle__label">Show Pending</span>
      </div>
    </div>
  );
}
