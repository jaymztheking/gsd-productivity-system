import { useEffect, useState } from "react";
import { useRoutine } from "../hooks/useRoutine";
import type {
  RoutineItem,
  RoutineTodayItem,
  Weekday,
} from "../types/models";

const WEEKDAYS: { day: Weekday; short: string; long: string }[] = [
  { day: 0, short: "Mon", long: "Monday" },
  { day: 1, short: "Tue", long: "Tuesday" },
  { day: 2, short: "Wed", long: "Wednesday" },
  { day: 3, short: "Thu", long: "Thursday" },
  { day: 4, short: "Fri", long: "Friday" },
  { day: 5, short: "Sat", long: "Saturday" },
  { day: 6, short: "Sun", long: "Sunday" },
];
const EVERY_DAY: Weekday[] = [0, 1, 2, 3, 4, 5, 6];

function describeDays(days: Weekday[]): string {
  const key = days.join(",");
  if (key === "0,1,2,3,4,5,6") return "Every day";
  if (key === "0,1,2,3,4") return "Weekdays";
  if (key === "5,6") return "Weekends";
  return days.map((d) => WEEKDAYS[d].short).join(", ");
}

function formatDate(isoDate: string): string {
  // Parse as a calendar date; new Date("YYYY-MM-DD") would be UTC midnight
  // and can display as the previous day in the browser's timezone.
  const [y, m, d] = isoDate.split("-").map(Number);
  return new Date(y, m - 1, d).toLocaleDateString(undefined, {
    weekday: "long",
    month: "short",
    day: "numeric",
  });
}

type View = "today" | "edit";

export default function RoutinePage() {
  const routine = useRoutine();
  const [view, setView] = useState<View>("today");

  if (routine.loading || !routine.today) {
    return <div className="loading">Loading routine...</div>;
  }

  return (
    <div className="stack stack--md">
      <div className="project-list-header">
        <div>
          <h2 className="page-title">Routine</h2>
          <div className="routine-date">{formatDate(routine.today.date)}</div>
        </div>
        <div className="segmented" role="tablist" aria-label="Routine view">
          {(["today", "edit"] as const).map((v) => (
            <button
              key={v}
              role="tab"
              aria-selected={view === v}
              className={`segmented__btn ${
                view === v ? "segmented__btn--active" : ""
              }`}
              onClick={() => setView(v)}
            >
              {v === "today" ? "Today" : "Edit"}
            </button>
          ))}
        </div>
      </div>

      {view === "today" ? (
        <TodayView
          items={routine.today.items}
          weekday={routine.today.weekday}
          onToggle={routine.setCompleted}
          onEdit={() => setView("edit")}
        />
      ) : (
        <EditView
          items={routine.items}
          todayWeekday={routine.today.weekday}
          onCreate={routine.createItem}
          onUpdate={routine.updateItem}
          onDelete={routine.deleteItem}
          onReorder={routine.reorder}
        />
      )}
    </div>
  );
}

// --- Today: the checklist ---

function TodayView({
  items,
  weekday,
  onToggle,
  onEdit,
}: {
  items: RoutineTodayItem[];
  weekday: Weekday;
  onToggle: (id: string, completed: boolean) => Promise<void>;
  onEdit: () => void;
}) {
  if (items.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-state__title">
          Nothing scheduled for {WEEKDAYS[weekday].long}
        </div>
        <p>Add routine items and choose the days they repeat.</p>
        <button className="btn btn--primary" onClick={onEdit}>
          Edit routine
        </button>
      </div>
    );
  }

  const done = items.filter((i) => i.completed).length;

  return (
    <div className="stack stack--sm">
      <div className="routine-progress">
        <span>
          {done} of {items.length} done
        </span>
        <div
          className="routine-progress__bar"
          role="progressbar"
          aria-valuemin={0}
          aria-valuemax={items.length}
          aria-valuenow={done}
          aria-label="Routine progress"
        >
          <div
            className="routine-progress__fill"
            style={{ width: `${(done / items.length) * 100}%` }}
          />
        </div>
      </div>
      <ul className="stack stack--xs routine-list">
        {items.map((item) => (
          <li key={item.id}>
            <button
              role="checkbox"
              aria-checked={item.completed}
              className={`routine-check ${
                item.completed ? "routine-check--done" : ""
              }`}
              onClick={() => onToggle(item.id, !item.completed)}
            >
              <span className="routine-check__box" aria-hidden="true">
                {item.completed ? "✓" : ""}
              </span>
              <span className="routine-check__title">{item.title}</span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

// --- Edit: manage the standing list ---

type DayFilter = Weekday | "all";

function EditView({
  items,
  todayWeekday,
  onCreate,
  onUpdate,
  onDelete,
  onReorder,
}: {
  items: RoutineItem[];
  todayWeekday: Weekday;
  onCreate: (title: string, weekdays: Weekday[]) => Promise<void>;
  onUpdate: (
    id: string,
    data: { title?: string; weekdays?: Weekday[] }
  ) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
  onReorder: (orderedIds: string[]) => Promise<void>;
}) {
  const [filter, setFilter] = useState<DayFilter>(todayWeekday);
  const [editingId, setEditingId] = useState<string | null>(null);

  const visible =
    filter === "all" ? items : items.filter((i) => i.weekdays.includes(filter));

  const move = async (index: number, direction: "up" | "down") => {
    const target = direction === "up" ? index - 1 : index + 1;
    const ids = visible.map((i) => i.id);
    [ids[index], ids[target]] = [ids[target], ids[index]];
    await onReorder(ids);
  };

  return (
    <div className="stack stack--md">
      <AddItemForm
        defaultDays={filter === "all" ? EVERY_DAY : [filter]}
        onCreate={onCreate}
      />

      <div
        className="day-filter"
        role="radiogroup"
        aria-label="Show items scheduled on"
      >
        {[
          { key: "all" as DayFilter, label: "All" },
          ...WEEKDAYS.map((w) => ({ key: w.day as DayFilter, label: w.short })),
        ].map(({ key, label }) => (
          <button
            key={label}
            role="radio"
            aria-checked={filter === key}
            className={`day-chip ${filter === key ? "day-chip--on" : ""}`}
            onClick={() => {
              setFilter(key);
              setEditingId(null);
            }}
          >
            {label}
          </button>
        ))}
      </div>

      {visible.length === 0 ? (
        <div className="text-muted routine-empty-filter">
          {filter === "all"
            ? "No routine items yet."
            : `Nothing scheduled on ${WEEKDAYS[filter].long}.`}
        </div>
      ) : (
        <div className="stack stack--xs">
          {visible.map((item, idx) =>
            editingId === item.id ? (
              <ItemEditor
                key={item.id}
                item={item}
                onSave={async (data) => {
                  await onUpdate(item.id, data);
                  setEditingId(null);
                }}
                onDelete={async () => {
                  await onDelete(item.id);
                  setEditingId(null);
                }}
                onCancel={() => setEditingId(null)}
              />
            ) : (
              <div key={item.id} className="task-order-row">
                <div className="task-order-row__arrows">
                  <button
                    className="order-btn"
                    disabled={idx === 0}
                    onClick={() => move(idx, "up")}
                    aria-label={`Move ${item.title} up`}
                  >
                    ▲
                  </button>
                  <button
                    className="order-btn"
                    disabled={idx === visible.length - 1}
                    onClick={() => move(idx, "down")}
                    aria-label={`Move ${item.title} down`}
                  >
                    ▼
                  </button>
                </div>
                <div className="task-order-row__content">
                  <div className="task-order-row__title">{item.title}</div>
                  <div className="routine-days">
                    {describeDays(item.weekdays)}
                  </div>
                </div>
                <button
                  className="btn btn--ghost btn--sm"
                  onClick={() => setEditingId(item.id)}
                  aria-label={`Edit ${item.title}`}
                >
                  Edit
                </button>
              </div>
            )
          )}
        </div>
      )}
    </div>
  );
}

function DayPicker({
  days,
  onChange,
}: {
  days: Weekday[];
  onChange: (days: Weekday[]) => void;
}) {
  const toggle = (day: Weekday) =>
    onChange(
      days.includes(day)
        ? days.filter((d) => d !== day)
        : [...days, day].sort((a, b) => a - b)
    );

  return (
    <div className="day-picker" role="group" aria-label="Repeat on">
      {WEEKDAYS.map((w) => (
        <button
          key={w.day}
          type="button"
          aria-pressed={days.includes(w.day)}
          aria-label={w.long}
          className={`day-chip ${days.includes(w.day) ? "day-chip--on" : ""}`}
          onClick={() => toggle(w.day)}
        >
          {w.short}
        </button>
      ))}
    </div>
  );
}

function AddItemForm({
  defaultDays,
  onCreate,
}: {
  defaultDays: Weekday[];
  onCreate: (title: string, weekdays: Weekday[]) => Promise<void>;
}) {
  const [title, setTitle] = useState("");
  const [days, setDays] = useState<Weekday[]>(defaultDays);
  const [saving, setSaving] = useState(false);

  // Follow the day filter until the user starts typing a new item
  const defaultKey = defaultDays.join(",");
  useEffect(() => {
    if (!title) setDays(defaultKey.split(",").map(Number) as Weekday[]);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [defaultKey]);

  const canSave = title.trim() !== "" && days.length > 0 && !saving;

  const submit = async () => {
    if (!canSave) return;
    setSaving(true);
    try {
      await onCreate(title.trim(), days);
      setTitle("");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="card stack stack--sm">
      <div className="capture-form">
        <input
          type="text"
          className="input"
          placeholder="Add a routine item..."
          aria-label="New routine item"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && submit()}
        />
        <button className="btn btn--primary" onClick={submit} disabled={!canSave}>
          Add
        </button>
      </div>
      <DayPicker days={days} onChange={setDays} />
    </div>
  );
}

function ItemEditor({
  item,
  onSave,
  onDelete,
  onCancel,
}: {
  item: RoutineItem;
  onSave: (data: { title: string; weekdays: Weekday[] }) => Promise<void>;
  onDelete: () => Promise<void>;
  onCancel: () => void;
}) {
  const [title, setTitle] = useState(item.title);
  const [days, setDays] = useState<Weekday[]>(item.weekdays);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const canSave = title.trim() !== "" && days.length > 0;

  return (
    <div className="card stack stack--sm">
      <input
        type="text"
        className="input"
        aria-label="Routine item name"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && canSave)
            onSave({ title: title.trim(), weekdays: days });
          if (e.key === "Escape") onCancel();
        }}
        autoFocus
      />
      <DayPicker days={days} onChange={setDays} />
      {days.length === 0 && (
        <div className="routine-hint">Pick at least one day.</div>
      )}
      <div className="btn-row routine-editor-actions">
        <button
          className="btn btn--primary btn--sm"
          disabled={!canSave}
          onClick={() => onSave({ title: title.trim(), weekdays: days })}
        >
          Save
        </button>
        <button className="btn btn--ghost btn--sm" onClick={onCancel}>
          Cancel
        </button>
        <span className="routine-editor-actions__spacer" />
        {confirmDelete ? (
          <button className="btn btn--danger btn--sm" onClick={onDelete}>
            Confirm delete
          </button>
        ) : (
          <button
            className="btn btn--danger-outline btn--sm"
            onClick={() => setConfirmDelete(true)}
          >
            Delete
          </button>
        )}
      </div>
    </div>
  );
}
