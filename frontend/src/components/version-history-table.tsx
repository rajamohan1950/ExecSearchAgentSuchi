"use client";

import { useState } from "react";
import type { ProfileVersionSummary } from "@/types/profile";
import { formatDate } from "@/lib/utils";

const PAGE_SIZE = 5;

interface VersionHistoryTableProps {
  versions: ProfileVersionSummary[];
  onView: (versionId: string) => void;
  activeVersionId?: string;
}

export default function VersionHistoryTable({
  versions,
  onView,
  activeVersionId,
}: VersionHistoryTableProps) {
  const [page, setPage] = useState(0);

  if (versions.length === 0) {
    return (
      <p className="text-sm text-gray-500">No profile versions yet.</p>
    );
  }

  const totalPages = Math.ceil(versions.length / PAGE_SIZE);
  const pagedVersions = versions.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  return (
    <div className="overflow-hidden rounded-lg bg-white shadow-sm border border-gray-100">
      <table className="w-full">
        <thead>
          <tr className="border-b border-gray-200 bg-gray-50 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
            <th className="px-4 py-3 w-12">#</th>
            <th className="px-4 py-3">Date</th>
            <th className="px-4 py-3">Source</th>
            <th className="px-4 py-3">Headline</th>
            <th className="px-4 py-3 w-28">Version</th>
            <th className="px-4 py-3 w-20"></th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {pagedVersions.map((v, i) => (
            <tr
              key={v.id}
              className={`hover:bg-gray-50 transition-colors ${
                activeVersionId === v.id ? "bg-blue-50" : ""
              }`}
            >
              <td className="px-4 py-3 text-sm text-gray-900">
                {versions.length - (page * PAGE_SIZE + i)}
              </td>
              <td className="px-4 py-3 text-sm text-gray-600">
                {formatDate(v.created_at)}
              </td>
              <td className="px-4 py-3 text-sm text-gray-600">
                {v.source_filename || v.source_type}
              </td>
              <td className="px-4 py-3 text-sm text-gray-600 max-w-xs truncate">
                {v.headline || "-"}
              </td>
              <td className="px-4 py-3 text-sm">
                <span className="inline-flex items-center gap-1">
                  v{v.version}
                  {v.is_current && (
                    <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">
                      Current
                    </span>
                  )}
                </span>
              </td>
              <td className="px-4 py-3 text-right">
                <button
                  onClick={() => onView(v.id)}
                  className={`rounded-md px-3 py-1 text-sm font-medium transition-colors ${
                    activeVersionId === v.id
                      ? "bg-blue-600 text-white"
                      : "bg-blue-50 text-blue-700 hover:bg-blue-100"
                  }`}
                >
                  View
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between border-t border-gray-200 bg-gray-50 px-4 py-2">
          <p className="text-xs text-gray-500">
            Showing {page * PAGE_SIZE + 1}–{Math.min((page + 1) * PAGE_SIZE, versions.length)} of{" "}
            {versions.length} versions
          </p>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
              className="rounded px-2 py-1 text-xs font-medium text-gray-600 hover:bg-gray-200 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Prev
            </button>
            {Array.from({ length: totalPages }, (_, i) => (
              <button
                key={i}
                onClick={() => setPage(i)}
                className={`rounded px-2 py-1 text-xs font-medium ${
                  page === i
                    ? "bg-blue-600 text-white"
                    : "text-gray-600 hover:bg-gray-200"
                }`}
              >
                {i + 1}
              </button>
            ))}
            <button
              onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
              disabled={page === totalPages - 1}
              className="rounded px-2 py-1 text-xs font-medium text-gray-600 hover:bg-gray-200 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
