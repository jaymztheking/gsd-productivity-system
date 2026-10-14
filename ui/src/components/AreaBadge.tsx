export default function AreaBadge({ name }: { name: string }) {
  return (
    <span
      className="tag-badge"
      style={{ "--badge-color": "var(--color-area)" } as React.CSSProperties}
    >
      {name}
    </span>
  );
}
