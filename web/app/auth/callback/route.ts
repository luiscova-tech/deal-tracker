import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

// Completes the magic-link flow: Supabase redirects here with a `code`
// query param after the user clicks the emailed link; exchanging it for a
// session sets the auth cookies via lib/supabase/server.ts's cookie handler.
export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url);
  const code = searchParams.get("code");
  const next = searchParams.get("next") ?? "/dashboard";

  if (code) {
    const supabase = await createClient();
    const { error } = await supabase.auth.exchangeCodeForSession(code);
    if (!error) {
      return NextResponse.redirect(`${origin}${next}`);
    }
  }

  return NextResponse.redirect(`${origin}/login`);
}
