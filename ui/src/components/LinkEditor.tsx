import { useState } from "react";
import type { ProjectLink } from "../types/models";

interface LinkEditorProps {
  links: ProjectLink[];
  onAdd: (url: string, label: string) => Promise<void>;
  onEdit: (linkId: string, data: { url?: string; label?: string }) => Promise<void>;
  onRemove: (linkId: string) => Promise<void>;
}

export default function LinkEditor({
  links,
  onAdd,
  onEdit,
  onRemove,
}: LinkEditorProps) {
  const [showAdd, setShowAdd] = useState(false);
  const [addUrl, setAddUrl] = useState("");
  const [addLabel, setAddLabel] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editUrl, setEditUrl] = useState("");
  const [editLabel, setEditLabel] = useState("");

  const handleAdd = async () => {
    if (!addUrl.trim() || !addLabel.trim()) return;
    await onAdd(addUrl.trim(), addLabel.trim());
    setAddUrl("");
    setAddLabel("");
    setShowAdd(false);
  };

  const handleEditSave = async (linkId: string) => {
    await onEdit(linkId, {
      url: editUrl.trim() || undefined,
      label: editLabel.trim() || undefined,
    });
    setEditingId(null);
  };

  return (
    <div className="stack stack--sm">
      {links.map((link) =>
        editingId === link.id ? (
          <div key={link.id} className="stack stack--xs">
            <input
              className="input"
              value={editLabel}
              onChange={(e) => setEditLabel(e.target.value)}
              placeholder="Label"
              autoFocus
            />
            <input
              className="input"
              value={editUrl}
              onChange={(e) => setEditUrl(e.target.value)}
              placeholder="URL"
            />
            <div className="btn-row">
              <button
                className="btn btn--primary btn--sm"
                onClick={() => handleEditSave(link.id)}
              >
                Save
              </button>
              <button
                className="btn btn--ghost btn--sm"
                onClick={() => setEditingId(null)}
              >
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <div key={link.id} className="link-row">
            <a
              href={link.url}
              target="_blank"
              rel="noopener noreferrer"
              className="link-row__label"
            >
              {link.label}
            </a>
            <div className="link-row__actions">
              <button
                className="btn btn--ghost btn--sm"
                onClick={() => {
                  setEditingId(link.id);
                  setEditUrl(link.url);
                  setEditLabel(link.label);
                }}
              >
                ✎
              </button>
              <button
                className="btn btn--ghost btn--sm"
                onClick={() => onRemove(link.id)}
              >
                ✕
              </button>
            </div>
          </div>
        )
      )}

      {showAdd ? (
        <div className="stack stack--xs">
          <input
            className="input"
            value={addLabel}
            onChange={(e) => setAddLabel(e.target.value)}
            placeholder="Label (e.g. JIRA Board)"
            autoFocus
          />
          <input
            className="input"
            value={addUrl}
            onChange={(e) => setAddUrl(e.target.value)}
            placeholder="URL (e.g. https://jira.example.com/board/1)"
            onKeyDown={(e) => e.key === "Enter" && handleAdd()}
          />
          <div className="btn-row">
            <button
              className="btn btn--primary btn--sm"
              onClick={handleAdd}
              disabled={!addUrl.trim() || !addLabel.trim()}
            >
              Add Link
            </button>
            <button
              className="btn btn--ghost btn--sm"
              onClick={() => {
                setShowAdd(false);
                setAddUrl("");
                setAddLabel("");
              }}
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <button
          className="btn btn--ghost"
          onClick={() => setShowAdd(true)}
        >
          + Add Link
        </button>
      )}
    </div>
  );
}
