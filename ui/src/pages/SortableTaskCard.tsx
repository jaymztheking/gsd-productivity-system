import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import type { ComponentProps } from "react";
import TaskCard from "./TaskCard";

type SortableTaskCardProps = Omit<ComponentProps<typeof TaskCard>, "dragHandle">;

/**
 * A TaskCard that can be dragged by its grip. Only the grip starts a drag,
 * so tapping the card still opens the editor and swiping the list still
 * scrolls the page on a phone.
 */
export default function SortableTaskCard(props: SortableTaskCardProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    setActivatorNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: props.action.id });

  return (
    <div
      ref={setNodeRef}
      className={isDragging ? "sortable--dragging" : undefined}
      style={{ transform: CSS.Translate.toString(transform), transition }}
    >
      <TaskCard
        {...props}
        dragHandle={
          <button
            ref={setActivatorNodeRef}
            type="button"
            className="drag-handle"
            aria-label={`Drag to reorder: ${props.action.title}`}
            onClick={(e) => e.stopPropagation()}
            {...attributes}
            {...listeners}
          >
            ⠿
          </button>
        }
      />
    </div>
  );
}
