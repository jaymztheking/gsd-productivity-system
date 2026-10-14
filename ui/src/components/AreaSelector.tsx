import type { Area, Project } from "../types/models";

interface AreaSelectorProps {
  areas: Area[];
  selected: string | null;
  onSelect: (areaId: string | null) => void;
}

/** One area or none, chosen like a tag: tap to pick, tap again to clear. */
export default function AreaSelector({
  areas,
  selected,
  onSelect,
}: AreaSelectorProps) {
  if (areas.length === 0) return null;

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

/**
 * The area to show after the project changes in an editor. A task defaults
 * to its project's area, so the area follows the project unless the user
 * has picked a different one by hand.
 */
export function areaAfterProjectChange(
  projects: Project[],
  oldProjectId: string | null,
  newProjectId: string | null,
  currentArea: string | null
): string | null {
  const areaOf = (id: string | null) =>
    projects.find((p) => p.id === id)?.area_id ?? null;
  const followsProject =
    currentArea === null || currentArea === areaOf(oldProjectId);
  return followsProject ? areaOf(newProjectId) ?? currentArea : currentArea;
}
