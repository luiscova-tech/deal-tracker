import { verifySession } from "@/lib/supabase/dal";
import { Nav } from "@/components/Nav";

// Redirects to /login if there's no session. Note: per Next.js's own
// guidance, layouts don't re-run on client-side navigation between sibling
// pages, so this covers full page loads — each page under this group must
// also call verifySession() itself (cache()-deduped, so that's free).
export default async function ProtectedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  await verifySession();

  return (
    <div className="flex min-h-dvh flex-col">
      <Nav />
      <div className="flex-1">{children}</div>
    </div>
  );
}
