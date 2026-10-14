import { useNextActions } from "../hooks/useNextActions";
import TagBadge from "../components/TagBadge";

export default function SomedayPage() {
  const { actions, loading, updateAction, deleteAction, removeFromList } =
    useNextActions({ status: "someday" });

  const handlePromote = async (id: string) => {
    await updateAction(id, { status: "active" });
    removeFromList(id);
  };

  if (loading) {
    return <div className="loading">Loading someday list...</div>;
  }

  if (actions.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-state__icon">&#9729;</div>
        <div className="empty-state__title">Nothing on hold</div>
        <p>File inbox items here when you are not committed to them yet.</p>
      </div>
    );
  }

  return (
    <div className="stack stack--sm">
      <div className="inbox-counter">
        {actions.length} someday/maybe item{actions.length !== 1 ? "s" : ""}
      </div>
      {actions.map((action) => (
        <div key={action.id} className="card stack stack--sm">
          <div>
            <div style={{ fontWeight: 600, fontSize: "0.95rem" }}>
              {action.title}
            </div>
            {(action.tags.length > 0 || action.project) && (
              <div
                className="row gap-sm"
                style={{ flexWrap: "wrap", marginTop: "0.25rem" }}
              >
                {action.tags.map((t) => (
                  <TagBadge key={t.id} tag={t} />
                ))}
                {action.project && (
                  <span
                    style={{
                      fontSize: "0.75rem",
                      color: "var(--color-text-muted)",
                    }}
                  >
                    {action.project.name}
                  </span>
                )}
              </div>
            )}
            {action.notes && (
              <p
                style={{
                  fontSize: "0.8rem",
                  color: "var(--color-text-muted)",
                  marginTop: "0.25rem",
                }}
              >
                {action.notes}
              </p>
            )}
          </div>
          <div className="intake-actions">
            <button
              className="btn btn--danger-outline btn--sm"
              onClick={() => deleteAction(action.id)}
            >
              Delete
            </button>
            <button
              className="btn btn--primary btn--sm"
              onClick={() => handlePromote(action.id)}
              style={{ flex: 1 }}
            >
              Make Active
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
