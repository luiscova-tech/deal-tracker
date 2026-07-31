"use client";

import { useActionState, useEffect, useRef } from "react";
import {
  createWatchlistItem,
  updateWatchlistItem,
  type ActionState,
  type WatchlistItem,
} from "./actions";

const initialState: ActionState = {};

export function WatchlistItemForm({
  item,
  onSaved,
  onCancel,
}: {
  item?: WatchlistItem;
  onSaved?: () => void;
  onCancel?: () => void;
}) {
  const action = item
    ? updateWatchlistItem.bind(null, item.id)
    : createWatchlistItem;
  const [state, formAction, isPending] = useActionState(action, initialState);
  const formRef = useRef<HTMLFormElement>(null);
  const fieldId = item?.id ?? "new";

  useEffect(() => {
    if (state.success) {
      if (!item) {
        formRef.current?.reset();
      }
      onSaved?.();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state]);

  return (
    <form ref={formRef} action={formAction} className="space-y-3">
      <div>
        <label
          htmlFor={`name-${fieldId}`}
          className="block text-sm font-medium text-gray-700"
        >
          Name
        </label>
        <input
          id={`name-${fieldId}`}
          name="name"
          type="text"
          required
          defaultValue={item?.name}
          placeholder="e.g. Dyson V15"
          className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-base text-gray-900 focus:border-gray-500 focus:outline-none"
        />
      </div>

      <div>
        <label
          htmlFor={`location-${fieldId}`}
          className="block text-sm font-medium text-gray-700"
        >
          Location
        </label>
        <select
          id={`location-${fieldId}`}
          name="location"
          defaultValue={item?.location ?? "both"}
          className="mt-1 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-base text-gray-900 focus:border-gray-500 focus:outline-none"
        >
          <option value="mesa">Mesa</option>
          <option value="phoenix">Phoenix</option>
          <option value="both">Both</option>
        </select>
      </div>

      <div>
        <label
          htmlFor={`price-${fieldId}`}
          className="block text-sm font-medium text-gray-700"
        >
          Price ceiling (optional)
        </label>
        <input
          id={`price-${fieldId}`}
          name="price_ceiling"
          type="number"
          min="0.01"
          step="0.01"
          inputMode="decimal"
          defaultValue={item?.price_ceiling ?? undefined}
          placeholder="e.g. 150"
          className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-base text-gray-900 focus:border-gray-500 focus:outline-none"
        />
      </div>

      {state.error && <p className="text-sm text-red-600">{state.error}</p>}

      <div className="flex gap-2">
        <button
          type="submit"
          disabled={isPending}
          className="flex-1 rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {isPending ? "Saving…" : item ? "Save changes" : "Add item"}
        </button>
        {item && (
          <button
            type="button"
            onClick={onCancel}
            className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700"
          >
            Cancel
          </button>
        )}
      </div>
    </form>
  );
}
