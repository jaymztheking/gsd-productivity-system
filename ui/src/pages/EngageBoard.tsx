import {
  DndContext,
  KeyboardSensor,
  PointerSensor,
  closestCorners,
  useDroppable,
  useSensor,
  useSensors,
  type DragEndEvent,
  type DragOverEvent,
  type DragStartEvent,
  type UniqueIdentifier,
} from "@dnd-kit/core";
import {
  SortableContext,
  arrayMove,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { useRef, type ComponentProps } from "react";
import type { Area, NextAction } from "../types/models";
import SortableTaskCard from "./SortableTaskCard";

const UNASSIGNED = "unassigned";

type CardProps = Omit<
  ComponentProps<typeof SortableTaskCard>,
  "action" | "areas"
>;

interface EngageBoardProps extends CardProps {
  /** The shown tasks, already filtered, in the shared Engage order */
  actions: NextAction[];
  areas: Area[];
  /** Replace the shown tasks locally (optimistic update while dragging) */
  onActionsChange: (actions: NextAction[]) => void;
  /**
   * Persist a drop: the task's new area if it changed column, then the new
   * order of the column it landed in.
   */
  onDrop: (
    taskId: string,
    newAreaId: string | null | undefined,
    columnOrder: string[]
  ) => Promise<void>;
}

function columnOf(action: NextAction): string {
  return action.area_id ?? UNASSIGNED;
}

/**
 * Engage as a board: one column per area, in area order, plus Unassigned.
 * Columns are filtered views of the one Engage order, so dragging within a
 * column reorders, and dragging to another column changes the task's area.
 */
export default function EngageBoard({
  actions,
  areas,
  onActionsChange,
  onDrop,
  ...cardProps
}: EngageBoardProps) {
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  // The area the dragged task had when the drag began
  const startColumn = useRef<string | null>(null);

  const columns = [
    ...areas.map((a) => ({ key: a.id, name: a.name })),
    { key: UNASSIGNED, name: "Unassigned" },
  ];
  const columnKeys = new Set(columns.map((c) => c.key));

  const containerOf = (id: UniqueIdentifier): string | undefined => {
    if (columnKeys.has(String(id))) return String(id);
    const action = actions.find((a) => a.id === id);
    return action ? columnOf(action) : undefined;
  };

  const handleDragStart = ({ active }: DragStartEvent) => {
    startColumn.current = containerOf(active.id) ?? null;
  };

  // Moving into another column re-files the card there as the pointer
  // crosses, so the destination column makes room for it before the drop.
  const handleDragOver = ({ active, over }: DragOverEvent) => {
    if (!over) return;
    const from = containerOf(active.id);
    const to = containerOf(over.id);
    if (!from || !to || from === to) return;

    const index = actions.findIndex((a) => a.id === active.id);
    const moved = { ...actions[index], area_id: to === UNASSIGNED ? null : to };
    const rest = actions.filter((a) => a.id !== active.id);

    let insertAt: number;
    if (columnKeys.has(String(over.id))) {
      // Over the column itself (empty, or below its cards): go last in it
      const lastInColumn = rest.reduce(
        (last, a, i) => (columnOf(a) === to ? i : last),
        -1
      );
      insertAt = lastInColumn === -1 ? rest.length : lastInColumn + 1;
    } else {
      insertAt = rest.findIndex((a) => a.id === over.id);
    }
    rest.splice(insertAt, 0, moved);
    onActionsChange(rest);
  };

  const handleDragEnd = async ({ active, over }: DragEndEvent) => {
    const column = containerOf(active.id);
    const began = startColumn.current;
    startColumn.current = null;
    if (!over || !column) return;

    let next = actions;
    if (over.id !== active.id && !columnKeys.has(String(over.id))) {
      const from = actions.findIndex((a) => a.id === active.id);
      const to = actions.findIndex((a) => a.id === over.id);
      next = arrayMove(actions, from, to);
      onActionsChange(next);
    }

    const columnOrder = next
      .filter((a) => columnOf(a) === column)
      .map((a) => a.id);
    const newArea =
      column === began ? undefined : column === UNASSIGNED ? null : column;
    await onDrop(String(active.id), newArea, columnOrder);
  };

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCorners}
      onDragStart={handleDragStart}
      onDragOver={handleDragOver}
      onDragEnd={handleDragEnd}
    >
      <div className="engage-board">
        {columns.map((column) => {
          const items = actions.filter((a) => columnOf(a) === column.key);
          return (
            <BoardColumn
              key={column.key}
              id={column.key}
              name={column.name}
              count={items.length}
            >
              <SortableContext
                items={items.map((a) => a.id)}
                strategy={verticalListSortingStrategy}
              >
                {items.map((action) => (
                  <SortableTaskCard
                    key={action.id}
                    action={action}
                    areas={areas}
                    {...cardProps}
                  />
                ))}
              </SortableContext>
            </BoardColumn>
          );
        })}
      </div>
    </DndContext>
  );
}

function BoardColumn({
  id,
  name,
  count,
  children,
}: {
  id: string;
  name: string;
  count: number;
  children: React.ReactNode;
}) {
  // The column body is a drop target too, so an empty column can take cards
  const { setNodeRef, isOver } = useDroppable({ id });
  return (
    <section className="engage-column" aria-label={`${name} (${count})`}>
      <header className="engage-column__header">
        <span className="engage-column__name">{name}</span>
        <span className="engage-column__count">{count}</span>
      </header>
      <div
        ref={setNodeRef}
        className={`engage-column__body ${isOver ? "engage-column__body--over" : ""}`}
      >
        {children}
        {count === 0 && <div className="engage-column__empty">No tasks</div>}
      </div>
    </section>
  );
}
