"use server";

import { revalidatePath } from "next/cache";
import { createClient } from "@/lib/supabase/server";

export type WatchlistItem = {
  id: string;
  name: string;
  location: string | null;
  price_ceiling: number | null;
};

export type ActionState = {
  error?: string;
  success?: boolean;
};

type ParsedForm =
  | { ok: true; name: string; location: string | null; priceCeiling: number | null }
  | { ok: false; error: string };

function parseWatchlistForm(formData: FormData): ParsedForm {
  const name = formData.get("name")?.toString().trim() ?? "";
  if (!name) {
    return { ok: false, error: "Name is required." };
  }

  const locationRaw = formData.get("location")?.toString() ?? "";
  const location = locationRaw === "mesa" || locationRaw === "phoenix" ? locationRaw : null;

  const priceCeilingRaw = formData.get("price_ceiling")?.toString().trim() ?? "";
  let priceCeiling: number | null = null;
  if (priceCeilingRaw) {
    priceCeiling = Number(priceCeilingRaw);
    if (!Number.isFinite(priceCeiling) || priceCeiling <= 0) {
      return { ok: false, error: "Price ceiling must be a positive number." };
    }
  }

  return { ok: true, name, location, priceCeiling };
}

export async function createWatchlistItem(
  _prevState: ActionState,
  formData: FormData
): Promise<ActionState> {
  const parsed = parseWatchlistForm(formData);
  if (!parsed.ok) return { error: parsed.error };

  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) return { error: "Not signed in." };

  const { error } = await supabase.from("watchlist_items").insert({
    user_id: user.id,
    name: parsed.name,
    site: "nellis",
    location: parsed.location,
    price_ceiling: parsed.priceCeiling,
  });

  if (error) {
    console.error("createWatchlistItem failed", error);
    return { error: "Couldn't save this item. Please try again." };
  }

  revalidatePath("/dashboard");
  return { success: true };
}

export async function updateWatchlistItem(
  id: string,
  _prevState: ActionState,
  formData: FormData
): Promise<ActionState> {
  const parsed = parseWatchlistForm(formData);
  if (!parsed.ok) return { error: parsed.error };

  const supabase = await createClient();
  const { error } = await supabase
    .from("watchlist_items")
    .update({
      name: parsed.name,
      location: parsed.location,
      price_ceiling: parsed.priceCeiling,
    })
    .eq("id", id);

  if (error) {
    console.error("updateWatchlistItem failed", error);
    return { error: "Couldn't save this item. Please try again." };
  }

  revalidatePath("/dashboard");
  return { success: true };
}

// prevState/formData are unused (delete needs neither), but useActionState
// requires this exact signature for the bound action passed to it.
export async function deleteWatchlistItem(
  id: string,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  _prevState: ActionState,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  _formData: FormData
): Promise<ActionState> {
  const supabase = await createClient();
  const { error } = await supabase.from("watchlist_items").delete().eq("id", id);

  if (error) {
    console.error("deleteWatchlistItem failed", error);
    return { error: "Couldn't delete this item. Please try again." };
  }

  revalidatePath("/dashboard");
  return { success: true };
}
