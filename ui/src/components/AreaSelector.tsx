import type { Area, Project } from "../types/models";
import AreaBadge from "./AreaBadge";

interface AreaSelectorProps {
  areas: Area[];
  selected: string | null;
  onSelect: (areaId: string | null) => void;
  /** The task's project. A task in a project always has the project's area,
   * so the picker is replaced by a read-only note. */
  project?: Project | null;
}

/** One area or none, chosen like a tag: tap to pick, tap again to clear. */
export default function AreaSelector({
  areas,
  selected,
  onSelect,
  project,
}: AreaSelectorProps) {
  if (areas.length === 0) return null;

  if (project) {
    const area = areas.find((a) => a.id === project.area_id);
    return (
      <div className="tag-selector">
        <span className="tag-selector__label">Area</span>
        <div className="area-inherited">
          {area ? <AreaBadge name={area.name} /> : <span>None</span>}
          <span className="text-muted">from project {project.name}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="tag-selector">
      <span className="tag-selector__label">Area</span>
      <div className="tag-selector__buttons">
        {areas.map((area) => {
          const isSelected = selected === area.id;
          return (
            <button
              key={area.id}
              type="button"
              className={`tag-btn ${isSelected ? "tag-btn--selected" : ""}`}
              style={{ "--btn-color": "var(--color-area)" } as React.CSSProperties}
              onClick={() => onSelect(isSelected ? null : area.id)}
            >
              {area.name}
            </button>
          );
        })}
      </div>
    </div>
  );
}

