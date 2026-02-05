"use client";

interface OutreachMetrics {
  total_firms: number;
  total_contacts: number;
  not_contacted: number;
  contacted: number;
  responded: number;
  in_conversation: number;
  converted: number;
  cold: number;
  emails_sent_today: number;
  emails_sent_total: number;
  response_rate_percent: number;
}

const METRIC_CARDS = [
  { key: "total_firms", label: "Total Firms", color: "bg-blue-50 text-blue-700" },
  { key: "total_contacts", label: "Contacts", color: "bg-indigo-50 text-indigo-700" },
  { key: "contacted", label: "Contacted", color: "bg-amber-50 text-amber-700" },
  { key: "responded", label: "Responded", color: "bg-green-50 text-green-700" },
  { key: "in_conversation", label: "In Conversation", color: "bg-emerald-50 text-emerald-700" },
  { key: "converted", label: "Converted", color: "bg-teal-50 text-teal-700" },
  { key: "cold", label: "Cold", color: "bg-gray-50 text-gray-600" },
  { key: "not_contacted", label: "Not Contacted", color: "bg-orange-50 text-orange-700" },
  { key: "emails_sent_today", label: "Sent Today", color: "bg-purple-50 text-purple-700" },
  { key: "emails_sent_total", label: "Total Sent", color: "bg-violet-50 text-violet-700" },
  { key: "response_rate_percent", label: "Response Rate", color: "bg-rose-50 text-rose-700", suffix: "%" },
] as const;

export default function MetricsPanel({ metrics }: { metrics: OutreachMetrics | null }) {
  if (!metrics) {
    return (
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {Array.from({ length: 11 }).map((_, i) => (
          <div key={i} className="animate-pulse rounded-xl bg-gray-100 h-20" />
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
      {METRIC_CARDS.map((card) => {
        const value = metrics[card.key as keyof OutreachMetrics];
        return (
          <div key={card.key} className={`rounded-xl p-4 ${card.color}`}>
            <div className="text-2xl font-bold">
              {value}
              {"suffix" in card ? card.suffix : ""}
            </div>
            <div className="text-xs font-medium mt-1 opacity-75">{card.label}</div>
          </div>
        );
      })}
    </div>
  );
}
