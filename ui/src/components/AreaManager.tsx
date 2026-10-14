import { useState } from "react";
import type { Area } from "../types/models";

interface AreaManagerProps {
  areas: Area[];
  onCreate: (name: string) => Promise<unknown>;
  onRename: (id: string, name: string) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
  onMove: (index: number, direction: "up" | "down") => Promise<void>;
}

/** Create, rename, reorder and delete areas of focus. */
export default function AreaManager({
  areas,
  onCreate,
  onRename,
  onDelete,
  onMove,
}: AreaManagerProps) {
  const [open, setOpen] = useState(false);
  const [newName, setNewName] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState("");
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // A duplicate name is the likely failure (409); show it rather than throw
  const attempt = async (fn: () => Promise<unknown>) => {
    setError(null);
    try {
      await fn();
      return true;
    } catch (e) {
      setError(
        e instanceof Error && e.message.includes("409")
          ? "An area with that name already exists."
          : "Could not save the area."
      );
      return false;
    }
  };

  const handleCreate = async () => {
    const name = newName.trim();
    if (!name) return;
    if (await attempt(() => onCreate(name))) setNewName("");
  };

  const handleRename = async (area: Area) => {
    const name = editName.trim();
    if (name && name !== area.name) {
      if (!(await attempt(() => onRename(area.id, name)))) return;
    }
    setEditingId(null);
  };

  return (
    <div className="stack stack--sm">
      <button
        className="btn btn--ghost section-toggle"
        onClick={() => setOpen(!open)}
      >
        {open ? "▾" : "▸"} Areas of focus ({areas.length})
      </button>

      {open && (
        <div className="stack stack--xs">
          {areas.map((area, idx) => (
            <div key={area.id} className="task-order-row">
              <div className="task-order-row__arrows">
                <button
                  className="order-btn"
                  disabled={idx === 0}
                  onClick={() => onMove(idx, "up")}
                  aria-label="Move up"
                >
                  ▲
                </button>
                <button
                  className="order-btn"
                  disabled={idx === areas.length - 1}
                  onClick={() => onMove(idx, "down")}
                  aria-label="Move down"
                >
                  ▼
                </button>
              </div>
              <div className="task-order-row__content">
                {editingId === area.id ? (
                  <input
                    className="input"
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                    onBlur={() => handleRename(area)}
                    onKeyDown={(e) => e.key === "Enter" && handleRename(area)}
                    autoFocus
                  />
                ) : (
                  <div
                    className="task-order-row__title"
                    onClick={() => {
                      setEditName(area.name);
                      setEditingId(area.id);
                      setConfirmDeleteId(null);
                    }}
                    style={{ cursor: "pointer" }}
                  >
                    {area.name}
                  </div>
                )}
              </div>
              {confirmDeleteId === area.id ? (
                <div className="btn-row">
                  <button
                    className="btn btn--danger btn--sm"
                    onClick={() => onDelete(area.id)}
                  >
                    Delete
                  </button>
                  <button
                    className="btn btn--ghost btn--sm"
                    onClick={() => setConfirmDeleteId(null)}
                  >
                    Keep
                  </button>
                </div>
              ) : (
                <button
                  className="btn btn--ghost btn--sm"
                  onClick={() => setConfirmDeleteId(area.id)}
                  aria-label={`Delete ${area.name}`}
                >
                  ✕
                </button>
              )}
            </div>
          ))}

          {confirmDeleteId && (
            <div className="text-muted" style={{ fontSize: "0.8rem" }}>
              Tasks and projects in this area are kept and become unassigned.
            </div>
          )}

          <div className="capture-form">
            <input
              className="input"
              placeholder="New area, e.g. Home life"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleCreate()}
            />
            <button
              className="btn btn--primary"
              onClick={handleCreate}
              disabled={!newName.trim()}
            >
              Add
            </button>
          </div>

          {error && (
            <div style={{ fontSize: "0.8rem", color: "var(--color-danger)" }}>
              {error}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
