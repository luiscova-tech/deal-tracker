"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const TABS = [
  { href: "/dashboard", label: "Watchlist" },
  { href: "/profile", label: "Profile" },
];

export function Nav() {
  const pathname = usePathname();

  return (
    <nav className="border-b border-gray-200">
      <div className="mx-auto flex max-w-sm">
        {TABS.map((tab) => {
          const isActive = pathname === tab.href;
          return (
            <Link
              key={tab.href}
              href={tab.href}
              className={`flex-1 border-b-2 px-4 py-3 text-center text-sm font-medium ${
                isActive ? "border-gray-900 text-gray-900" : "border-transparent text-gray-500"
              }`}
            >
              {tab.label}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
