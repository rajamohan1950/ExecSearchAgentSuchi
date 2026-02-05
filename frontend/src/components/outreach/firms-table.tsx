"use client";

import Link from "next/link";
import StatusBadge from "./status-badge";

interface FirmListItem {
  id: string;
  name: string;
  website: string | null;
  industry_focus: string | null;
  location: string | null;
  status: string;
  contact_count: number;
  created_at: string;
}

export default function FirmsTable({ firms }: { firms: FirmListItem[] }) {
  if (!firms || firms.length === 0) {
    return (
      <div className="rounded-xl border border-gray-200 bg-white p-12 text-center text-gray-500">
        No firms uploaded yet. Upload a CSV to get started.
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-xl border border-gray-200 bg-white">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">Firm</th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">Industry</th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">Location</th>
            <th className="px-4 py-3 text-center text-xs font-medium uppercase text-gray-500">Contacts</th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">Status</th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">Added</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {firms.map((firm) => (
            <tr key={firm.id} className="hover:bg-gray-50 transition-colors">
              <td className="px-4 py-3">
                <Link
                  href={`/outreach/firms/${firm.id}`}
                  className="text-sm font-medium text-blue-600 hover:text-blue-800"
                >
                  {firm.name}
                </Link>
                {firm.website && (
                  <div className="text-xs text-gray-400 mt-0.5">{firm.website}</div>
                )}
              </td>
              <td className="px-4 py-3 text-sm text-gray-600">{firm.industry_focus || "—"}</td>
              <td className="px-4 py-3 text-sm text-gray-600">{firm.location || "—"}</td>
              <td className="px-4 py-3 text-center text-sm font-medium text-gray-700">{firm.contact_count}</td>
              <td className="px-4 py-3">
                <StatusBadge status={firm.status} />
              </td>
              <td className="px-4 py-3 text-xs text-gray-400">
                {new Date(firm.created_at).toLocaleDateString()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
