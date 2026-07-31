"use server";

import { revalidatePath } from "next/cache";
import { createClient } from "@/lib/supabase/server";

export type ActionState = {
  error?: string;
  success?: boolean;
};

// Matches ntfy.sh's own topic naming rule, so we don't let someone save a
// topic that ntfy would never actually deliver to.
const NTFY_TOPIC_PATTERN = /^[-_a-zA-Z0-9]{1,64}$/;

export async function updateProfile(
  _prevState: ActionState,
  formData: FormData
): Promise<ActionState> {
  const raw = formData.get("ntfy_topic")?.toString().trim() ?? "";
  const ntfyTopic = raw === "" ? null : raw;

  if (ntfyTopic !== null && !NTFY_TOPIC_PATTERN.test(ntfyTopic)) {
    return {
      error: "Topic name can only contain letters, numbers, - and _, up to 64 characters.",
    };
  }

  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) return { error: "Not signed in." };

  // upsert (not update): the profiles row should already exist via the
  // on_auth_user_created trigger, but this stays correct even if it
  // somehow doesn't yet, rather than silently updating zero rows.
  const { error } = await supabase
    .from("profiles")
    .upsert({ id: user.id, email: user.email ?? "", ntfy_topic: ntfyTopic });

  if (error) {
    console.error("updateProfile failed", error);
    return { error: "Couldn't save your profile. Please try again." };
  }

  revalidatePath("/profile");
  return { success: true };
}
