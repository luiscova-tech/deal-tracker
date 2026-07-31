"use client";

import { useActionState } from "react";
import { Button } from "@/components/Button";
import { updateProfile, type ActionState } from "./actions";

const initialState: ActionState = {};

export function ProfileForm({ initialTopic }: { initialTopic: string }) {
  const [state, formAction, isPending] = useActionState(updateProfile, initialState);

  return (
    <form action={formAction} className="space-y-3">
      <div>
        <label htmlFor="ntfy_topic" className="block text-sm font-medium text-gray-700">
          ntfy topic
        </label>
        <input
          id="ntfy_topic"
          name="ntfy_topic"
          type="text"
          defaultValue={initialTopic}
          className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-base text-gray-900 focus:border-gray-500 focus:outline-none"
        />
        <p className="mt-2 text-sm text-gray-600">
          This is your private notification channel — install the{" "}
          <a
            href="https://ntfy.sh"
            target="_blank"
            rel="noopener noreferrer"
            className="underline"
          >
            ntfy app
          </a>{" "}
          and subscribe to this exact topic name to get alerts.
        </p>
      </div>

      {state.error && <p className="text-sm text-red-600">{state.error}</p>}
      {state.success && <p className="text-sm text-green-700">Saved.</p>}

      <Button type="submit" disabled={isPending} className="w-full">
        {isPending ? "Saving…" : "Save"}
      </Button>
    </form>
  );
}
