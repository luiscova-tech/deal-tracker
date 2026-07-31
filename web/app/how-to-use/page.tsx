import type { Metadata } from "next";
import Link from "next/link";
import { createClient } from "@/lib/supabase/server";

export const metadata: Metadata = {
  title: "How to Use — Deal Tracker",
};

export default async function HowToUsePage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  return (
    <main className="px-4 py-8">
      <div className="mx-auto max-w-sm space-y-8">
        <div>
          <Link href={user ? "/dashboard" : "/login"} className="text-sm text-gray-500 underline">
            {user ? "← Back to Watchlist" : "← Back to sign in"}
          </Link>
          <h1 className="mt-3 text-xl font-semibold text-gray-900">How This Works</h1>
          <p className="mt-1 text-sm text-gray-600">
            A quick guide to finding deals and getting notified — no tech experience needed.
          </p>
        </div>

        <ol className="space-y-6">
          <Step
            number={1}
            title="Sign in"
            cta={
              <Link
                href="/login"
                className="inline-block rounded-md bg-gray-900 px-4 py-2.5 text-sm font-medium text-white hover:bg-gray-800"
              >
                Go to sign-in
              </Link>
            }
          >
            Go to the sign-in page, type in your email address, and tap &ldquo;Send magic
            link.&rdquo; Check your email for a message from us and tap the link inside —
            that&rsquo;s it, no password to remember.
          </Step>

          <Step number={2} title="Add what you're looking for">
            On the Watchlist page, type the name of the item you want (like &ldquo;Arena
            Carbon&rdquo; or &ldquo;Dyson V15&rdquo;). Choose which warehouse — Mesa, Phoenix,
            or Both. If you only want to hear about it under a certain price, add a max price.
            Then tap &ldquo;Add item.&rdquo;
          </Step>

          <Step number={3} title="Turn on notifications">
            Go to your Profile page and install the free &ldquo;ntfy&rdquo; app (search
            &ldquo;ntfy&rdquo; in the App Store). Open it and subscribe to the exact topic name
            shown on your Profile page. That&rsquo;s it — you&rsquo;ll get a notification on
            your phone automatically whenever something you&rsquo;re watching for shows up. No
            need to keep checking the site.
          </Step>

          <Step number={4} title="See what's been found">
            The Watchlist page also shows &ldquo;Recent matches&rdquo; — a running list of
            everything found for you, with prices and links so you can take a look right away.
          </Step>
        </ol>
      </div>
    </main>
  );
}

function Step({
  number,
  title,
  cta,
  children,
}: {
  number: number;
  title: string;
  cta?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <li className="flex gap-4">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gray-900 text-sm font-semibold text-white">
        {number}
      </div>
      <div className="min-w-0">
        <h2 className="font-semibold text-gray-900">{title}</h2>
        <p className="mt-1 text-sm text-gray-600">{children}</p>
        {cta && <div className="mt-3">{cta}</div>}
      </div>
    </li>
  );
}
