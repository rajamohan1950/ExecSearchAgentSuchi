"use client";

interface AgentAction {
  id: string;
  contact_id: string | null;
  action_type: string;
  description: string | null;
  llm_model_used: string | null;
  status: string;
  error_message: string | null;
  created_at: string;
}

const ACTION_ICONS: Record<string, string> = {
  send_initial: "📤",
  send_followup: "🔄",
  analyze_response: "🔍",
  mark_cold: "🥶",
  mark_converted: "🎉",
  daily_briefing: "📊",
  error: "❌",
  task_error: "⚠️",
  skip: "⏭️",
  wait: "⏳",
};

export default function ActivityFeed({ actions }: { actions: AgentAction[] }) {
  if (!actions || actions.length === 0) {
    return (
      <div className="rounded-xl border border-gray-200 bg-white p-8 text-center text-gray-500">
        No agent activity yet. Upload firms and the agent will start working.
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {actions.map((action) => (
        <div
          key={action.id}
          className={`rounded-lg border p-3 text-sm ${
            action.status === "failed"
              ? "border-red-200 bg-red-50"
              : "border-gray-200 bg-white"
          }`}
        >
          <div className="flex items-start justify-between gap-2">
            <div className="flex items-center gap-2">
              <span className="text-lg">{ACTION_ICONS[action.action_type] || "🤖"}</span>
              <div>
                <span className="font-medium text-gray-800">
                  {action.action_type.replace(/_/g, " ")}
                </span>
                {action.description && (
                  <p className="mt-0.5 text-xs text-gray-500 line-clamp-2">
                    {action.description}
                  </p>
                )}
                {action.error_message && (
                  <p className="mt-0.5 text-xs text-red-600">{action.error_message}</p>
                )}
              </div>
            </div>
            <div className="flex flex-col items-end text-xs text-gray-400 shrink-0">
              <span>{new Date(action.created_at).toLocaleTimeString()}</span>
              <span>{new Date(action.created_at).toLocaleDateString()}</span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
