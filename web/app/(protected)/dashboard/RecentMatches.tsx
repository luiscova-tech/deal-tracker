export type RecentMatch = {
  id: string;
  watchlistItemName: string | null;
  title: string | null;
  price: number | null;
  url: string | null;
  firstSeenAt: string;
};

const RELATIVE_TIME_UNITS: [Intl.RelativeTimeFormatUnit, number][] = [
  ["year", 31536000],
  ["month", 2592000],
  ["week", 604800],
  ["day", 86400],
  ["hour", 3600],
  ["minute", 60],
];

// No date library needed for something this simple — Intl.RelativeTimeFormat
// is built into Node/browsers already.
function formatRelativeTime(isoString: string): string {
  const seconds = Math.round((Date.now() - new Date(isoString).getTime()) / 1000);

  for (const [unit, secondsInUnit] of RELATIVE_TIME_UNITS) {
    const value = Math.floor(seconds / secondsInUnit);
    if (value >= 1) {
      return new Intl.RelativeTimeFormat("en", { numeric: "auto" }).format(-value, unit);
    }
  }
  return "just now";
}

export function RecentMatches({ matches }: { matches: RecentMatch[] }) {
  if (matches.length === 0) {
    return <p className="mt-3 text-sm text-gray-500">No matches yet</p>;
  }

  return (
    <ul className="mt-3 space-y-3">
      {matches.map((match) => (
        <li key={match.id} className="rounded-md border border-gray-200 p-3">
          <p className="text-xs font-medium tracking-wide text-gray-500 uppercase">
            {match.watchlistItemName ?? "Unknown item"}
          </p>
          <p className="mt-1 font-medium text-gray-900">
            {match.url ? (
              <a href={match.url} target="_blank" rel="noopener noreferrer" className="underline">
                {match.title ?? "View listing"}
              </a>
            ) : (
              (match.title ?? "View listing")
            )}
          </p>
          <p className="mt-0.5 text-sm text-gray-600">
            {match.price != null && `$${match.price} · `}
            {formatRelativeTime(match.firstSeenAt)}
          </p>
        </li>
      ))}
    </ul>
  );
}
