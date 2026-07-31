// Next.js only inlines `NEXT_PUBLIC_` vars into the browser bundle when it
// sees a literal `process.env.NEXT_PUBLIC_X` reference — a dynamic
// `process.env[name]` lookup can't be statically replaced, so it silently
// resolves to undefined client-side even though the value is set. Keep the
// actual reads literal; only the validation logic is shared.
function requireEnv(name: string, value: string | undefined): string {
  if (!value) {
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return value;
}

export const supabaseUrl = requireEnv(
  "NEXT_PUBLIC_SUPABASE_URL",
  process.env.NEXT_PUBLIC_SUPABASE_URL
);
export const supabasePublishableKey = requireEnv(
  "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY",
  process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY
);
