"use client";

import { useActionState, useState } from "react";
import { Button } from "@/components/Button";
import { deleteWatchlistItem, type ActionState, type WatchlistItem } from "./actions";
import { WatchlistItemForm } from "./WatchlistItemForm";

const LOCATION_LABELS: Record<string, string> = {
  mesa: "Mesa",
  phoenix: "Phoenix",
};

export function WatchlistList({ items }: { items: WatchlistItem[] }) {
  const [editingId, setEditingId] = useState<string | null>(null);

  if (items.length === 0) {
    return (
      <p className="mt-3 text-sm text-gray-500">No items yet — add one below.</p>
    );
  }

  return (
    <ul className="mt-3 space-y-3">
      {items.map((item) => (
        <li key={item.id} className="rounded-md border border-gray-200 p-3">
          {editingId === item.id ? (
            <WatchlistItemForm
              item={item}
              onSaved={() => setEditingId(null)}
              onCancel={() => setEditingId(null)}
            />
          ) : (
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="truncate font-medium text-gray-900">{item.name}</p>
                <p className="mt-0.5 text-sm text-gray-600">
                  {item.location ? LOCATION_LABELS[item.location] ?? item.location : "Both"}
                  {item.price_ceiling != null && ` · up to $${item.price_ceiling}`}
                </p>
              </div>
              <div className="flex shrink-0 items-start gap-1">
                <Button type="button" variant="ghost" onClick={() => setEditingId(item.id)}>
                  Edit
                </Button>
                <DeleteButton id={item.id} name={item.name} />
              </div>
            </div>
          )}
        </li>
      ))}
    </ul>
  );
}

const initialDeleteState: ActionState = {};

function DeleteButton({ id, name }: { id: string; name: string }) {
  const [state, formAction, isPending] = useActionState(
    deleteWatchlistItem.bind(null, id),
    initialDeleteState
  );

  return (
    <form
      action={formAction}
      onSubmit={(event) => {
        if (!confirm(`Delete "${name}"?`)) {
          event.preventDefault();
        }
      }}
    >
      <Button type="submit" variant="danger" disabled={isPending}>
        {isPending ? "Deleting…" : "Delete"}
      </Button>
      {state.error && <p className="mt-1 text-xs text-red-600">{state.error}</p>}
    </form>
  );
}
