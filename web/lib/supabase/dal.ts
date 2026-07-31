import "server-only";
import { cache } from "react";
import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";

// Next.js's own guidance: auth checks in a shared layout don't re-run on
// client-side navigation between sibling pages, so this must be called
// from each protected page itself, not just from app/(protected)/layout.tsx.
// cache() dedupes it if a page and its layout both call it in one request.
export const verifySession = cache(async () => {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login");
  }

  return { user };
});
