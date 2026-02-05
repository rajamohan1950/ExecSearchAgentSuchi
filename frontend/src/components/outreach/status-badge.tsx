"use client";

const STATUS_COLORS: Record<string, string> = {
  new: "bg-blue-100 text-blue-700",
  active: "bg-blue-100 text-blue-700",
  contacted: "bg-amber-100 text-amber-700",
  responded: "bg-green-100 text-green-700",
  in_conversation: "bg-emerald-100 text-emerald-700",
  converted: "bg-teal-100 text-teal-700",
  cold: "bg-gray-100 text-gray-600",
  paused: "bg-yellow-100 text-yellow-700",
  exhausted: "bg-red-100 text-red-700",
  closed_positive: "bg-green-100 text-green-700",
  closed_negative: "bg-red-100 text-red-700",
};

export default function StatusBadge({ status }: { status: string }) {
  const color = STATUS_COLORS[status] || "bg-gray-100 text-gray-600";
  const label = status.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${color}`}>
      {label}
    </span>
  );
}
