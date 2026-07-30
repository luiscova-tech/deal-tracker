import { verifySession } from "@/lib/supabase/dal";

export default async function DashboardPage() {
  const { user } = await verifySession();

  return (
    <main className="min-h-dvh px-4 py-8">
      <div className="mx-auto max-w-sm">
        <h1 className="text-xl font-semibold text-gray-900">Dashboard</h1>
        <p className="mt-2 text-sm text-gray-600">
          Signed in as{" "}
          <span className="font-medium text-gray-900">{user.email}</span>
        </p>
        <p className="mt-6 text-sm text-gray-500">
          Watchlist and match history are coming next.
        </p>
      </div>
    </main>
  );
}
