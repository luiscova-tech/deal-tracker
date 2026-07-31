import { verifySession } from "@/lib/supabase/dal";
import { createClient } from "@/lib/supabase/server";
import { WatchlistList } from "./WatchlistList";
import { WatchlistItemForm } from "./WatchlistItemForm";

export default async function DashboardPage() {
  const { user } = await verifySession();

  const supabase = await createClient();
  const { data: items, error: itemsError } = await supabase
    .from("watchlist_items")
    .select("id, name, location, price_ceiling")
    .order("created_at", { ascending: false });

  if (itemsError) {
    console.error("Failed to load watchlist_items", itemsError);
  }

  return (
    <main className="min-h-dvh px-4 py-8">
      <div className="mx-auto max-w-sm space-y-8">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Dashboard</h1>
          <p className="mt-2 text-sm text-gray-600">
            Signed in as{" "}
            <span className="font-medium text-gray-900">{user.email}</span>
          </p>
        </div>

        <section>
          <h2 className="text-sm font-semibold tracking-wide text-gray-500 uppercase">
            Your watchlist
          </h2>
          {itemsError ? (
            <p className="mt-3 text-sm text-red-600">
              Couldn&rsquo;t load your watchlist. Try refreshing the page.
            </p>
          ) : (
            <WatchlistList items={items ?? []} />
          )}
        </section>

        <section>
          <h2 className="text-sm font-semibold tracking-wide text-gray-500 uppercase">
            Add item
          </h2>
          <div className="mt-3">
            <WatchlistItemForm />
          </div>
        </section>
      </div>
    </main>
  );
}
