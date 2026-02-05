"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getFirms, getOutreachMetrics, getAgentStatus } from "@/lib/api-client";
import MetricsPanel from "@/components/outreach/metrics-panel";
import FirmsTable from "@/components/outreach/firms-table";

export default function OutreachPage() {
  const [metrics, setMetrics] = useState<any>(null);
  const [firms, setFirms] = useState<any[]>([]);
  const [agentStatus, setAgentStatus] = useState<any>(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, [search, statusFilter]);

  async function loadData() {
    setLoading(true);
    try {
      const [m, f, s] = await Promise.all([
        getOutreachMetrics().catch(() => null),
        getFirms(search || undefined, statusFilter || undefined).catch(() => []),
        getAgentStatus().catch(() => null),
      ]);
      setMetrics(m);
      setFirms(f);
      setAgentStatus(s);
    } catch (e) {
      console.error("Failed to load outreach data:", e);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Outreach Agent</h1>
          <p className="text-sm text-gray-500 mt-1">
            Autonomous executive search outreach — Agent Suchi
          </p>
        </div>
        <div className="flex items-center gap-3">
          {agentStatus && (
            <div className="flex items-center gap-2 rounded-full bg-gray-100 px-3 py-1.5 text-xs">
              <span
                className={`h-2 w-2 rounded-full ${
                  agentStatus.scheduler_running ? "bg-green-500" : "bg-red-500"
                }`}
              />
              <span className="text-gray-600">
                {agentStatus.scheduler_running ? "Agent Running" : "Agent Stopped"}
              </span>
            </div>
          )}
          <Link
            href="/outreach/upload"
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
          >
            Upload Firms
          </Link>
          <Link
            href="/outreach/activity"
            className="rounded-lg bg-gray-100 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-200 transition-colors"
          >
            Activity Log
          </Link>
        </div>
      </div>

      {/* Metrics Panel */}
      <MetricsPanel metrics={metrics} />

      {/* Search & Filter */}
      <div className="flex items-center gap-3">
        <input
          type="text"
          placeholder="Search firms..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="flex-1 rounded-lg border border-gray-300 px-4 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
        >
          <option value="">All Statuses</option>
          <option value="new">New</option>
          <option value="active">Active</option>
          <option value="paused">Paused</option>
          <option value="exhausted">Exhausted</option>
          <option value="converted">Converted</option>
        </select>
        <button
          onClick={loadData}
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-600 hover:bg-gray-50"
        >
          Refresh
        </button>
      </div>

      {/* Firms Table */}
      {loading ? (
        <div className="animate-pulse space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-14 rounded-lg bg-gray-100" />
          ))}
        </div>
      ) : (
        <FirmsTable firms={firms} />
      )}
    </div>
  );
}
