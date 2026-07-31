import { createBrowserClient } from "@supabase/ssr";
import { supabasePublishableKey, supabaseUrl } from "@/lib/supabase/env";

// For use in Client Components.
export function createClient() {
  return createBrowserClient(supabaseUrl, supabasePublishableKey);
}
