"use client";

import { useEffect, useState } from "react";
import { getAgentActions, getAgentStatus } from "@/lib/api-client";
import ActivityFeed from "@/components/outreach/activity-feed";

export default function ActivityPage() {
  const [actions, setActions] = useState<any[]>([]);
  const [agentStatus, setAgentStatus] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
    // Auto-refresh every 30 seconds
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, []);

  async function loadData() {
    try {
      const [a, s] = await Promise.all([
        getAgentActions(100).catch(() => []),
        getAgentStatus().catch(() => null),
      ]);
      setActions(a);
      setAgentStatus(s);
    } catch (e) {
      console.error("Failed to load activity:", e);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Agent Activity Log</h1>
          <p className="text-sm text-gray-500 mt-1">
            Every decision and action by Agent Suchi — auto-refreshes every 30s
          </p>
        </div>
        <div className="flex items-center gap-3">
          {agentStatus && (
            <div className="text-xs text-gray-500 space-y-1 text-right">
              <div>
                Pending tasks: <span className="font-bold">{agentStatus.pending_tasks}</span>
              </div>
              {agentStatus.last_action_at && (
                <div>
                  Last action: {new Date(agentStatus.last_action_at).toLocaleString()}
                </div>
              )}
            </div>
          )}
          <button
            onClick={loadData}
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-600 hover:bg-gray-50"
          >
            Refresh
          </button>
        </div>
      </div>

      {loading ? (
        <div className="space-y-3">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="animate-pulse h-16 rounded-lg bg-gray-100" />
          ))}
        </div>
      ) : (
        <ActivityFeed actions={actions} />
      )}
    </div>
  );
}
