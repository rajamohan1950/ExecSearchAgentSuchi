"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { clearToken } from "@/lib/api-client";

export default function NavBar() {
  const router = useRouter();
  const pathname = usePathname();

  function handleLogout() {
    clearToken();
    router.push("/");
  }

  const links = [
    { href: "/dashboard", label: "Dashboard" },
    { href: "/profile", label: "Profile" },
    { href: "/upload", label: "Upload" },
  ];

  return (
    <nav className="border-b border-gray-200 bg-white">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-6">
        <Link href="/dashboard" className="text-xl font-bold text-gray-900 tracking-tight">
          Suchi
        </Link>
        <div className="flex items-center gap-1">
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={`rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                pathname === link.href
                  ? "bg-blue-50 text-blue-700"
                  : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
              }`}
            >
              {link.label}
            </Link>
          ))}
          <div className="ml-4 h-5 w-px bg-gray-200" />
          <button
            onClick={handleLogout}
            className="ml-2 rounded-lg px-3 py-2 text-sm text-gray-500 hover:bg-gray-50 hover:text-gray-700"
          >
            Sign out
          </button>
        </div>
      </div>
    </nav>
  );
}
