"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { getFirmDetail, triggerOutreach } from "@/lib/api-client";
import StatusBadge from "@/components/outreach/status-badge";

export default function FirmDetailPage() {
  const params = useParams();
  const firmId = params.firmId as string;
  const [firm, setFirm] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [triggeringId, setTriggeringId] = useState<string | null>(null);

  useEffect(() => {
    loadFirm();
  }, [firmId]);

  async function loadFirm() {
    setLoading(true);
    try {
      const data = await getFirmDetail(firmId);
      setFirm(data);
    } catch (e) {
      console.error("Failed to load firm:", e);
    } finally {
      setLoading(false);
    }
  }

  async function handleTrigger(contactId: string) {
    setTriggeringId(contactId);
    try {
      await triggerOutreach(contactId);
      // Reload to show updated status
      setTimeout(loadFirm, 2000);
    } catch (e: any) {
      alert(`Failed to trigger outreach: ${e.message}`);
    } finally {
      setTriggeringId(null);
    }
  }

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="animate-pulse h-8 w-64 rounded bg-gray-200" />
        <div className="animate-pulse h-64 rounded-xl bg-gray-100" />
      </div>
    );
  }

  if (!firm) {
    return <div className="text-center text-gray-500 py-12">Firm not found</div>;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <Link href="/outreach" className="text-xs text-blue-600 hover:text-blue-800">
            ← Back to Outreach
          </Link>
          <h1 className="text-2xl font-bold text-gray-900 mt-1">{firm.name}</h1>
          <div className="flex items-center gap-3 mt-1 text-sm text-gray-500">
            {firm.website && <span>{firm.website}</span>}
            {firm.industry_focus && <span>• {firm.industry_focus}</span>}
            {firm.location && <span>• {firm.location}</span>}
          </div>
        </div>
        <StatusBadge status={firm.status} />
      </div>

      {firm.notes && (
        <div className="rounded-lg bg-gray-50 p-4 text-sm text-gray-600">{firm.notes}</div>
      )}

      {/* Contacts */}
      <div>
        <h2 className="text-lg font-semibold text-gray-800 mb-3">
          Contacts ({firm.contacts?.length || 0})
        </h2>
        <div className="space-y-3">
          {(firm.contacts || []).map((contact: any) => (
            <div
              key={contact.id}
              className="flex items-center justify-between rounded-xl border border-gray-200 bg-white p-4"
            >
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-medium text-gray-800">{contact.name}</span>
                  {contact.is_primary && (
                    <span className="rounded-full bg-blue-100 px-2 py-0.5 text-xs text-blue-700">
                      Primary
                    </span>
                  )}
                  <StatusBadge status={contact.status} />
                </div>
                <div className="mt-1 text-sm text-gray-500">
                  {contact.email}
                  {contact.title && <span className="ml-2">• {contact.title}</span>}
                </div>
                {contact.last_contacted_at && (
                  <div className="mt-1 text-xs text-gray-400">
                    Last contacted: {new Date(contact.last_contacted_at).toLocaleDateString()}
                  </div>
                )}
              </div>
              <button
                onClick={() => handleTrigger(contact.id)}
                disabled={triggeringId === contact.id || contact.status === "cold"}
                className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                  triggeringId === contact.id
                    ? "bg-gray-100 text-gray-400 cursor-wait"
                    : contact.status === "cold"
                    ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                    : "bg-blue-50 text-blue-700 hover:bg-blue-100"
                }`}
              >
                {triggeringId === contact.id ? "Triggering..." : "Trigger Outreach"}
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
