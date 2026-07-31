import { verifySession } from "@/lib/supabase/dal";
import { createClient } from "@/lib/supabase/server";
import { WatchlistList } from "./WatchlistList";
import { WatchlistItemForm } from "./WatchlistItemForm";
import { RecentMatches, type RecentMatch } from "./RecentMatches";

type MatchRow = {
  id: string;
  title: string | null;
  price: number | null;
  url: string | null;
  first_seen_at: string;
  watchlist_items: { name: string } | null;
};

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

  // RLS scopes this to the signed-in user's own matches (their watchlist
  // items' seen_items rows) — see db/schema.sql's "Users can view their
  // own matches" policy.
  const { data: matchRows, error: matchesError } = await supabase
    .from("seen_items")
    .select("id, title, price, url, first_seen_at, watchlist_items!inner(name)")
    .order("first_seen_at", { ascending: false })
    .limit(20)
    .returns<MatchRow[]>();

  if (matchesError) {
    console.error("Failed to load recent matches", matchesError);
  }

  const matches: RecentMatch[] = (matchRows ?? []).map((row) => ({
    id: row.id,
    watchlistItemName: row.watchlist_items?.name ?? null,
    title: row.title,
    price: row.price,
    url: row.url,
    firstSeenAt: row.first_seen_at,
  }));

  return (
    <main className="px-4 py-8">
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
            Recent matches
          </h2>
          {matchesError ? (
            <p className="mt-3 text-sm text-red-600">
              Couldn&rsquo;t load recent matches. Try refreshing the page.
            </p>
          ) : (
            <RecentMatches matches={matches} />
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
