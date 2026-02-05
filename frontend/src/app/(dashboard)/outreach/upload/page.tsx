"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { uploadFirmsCSV } from "@/lib/api-client";
import CSVUploadZone from "@/components/outreach/csv-upload-zone";

export default function OutreachUploadPage() {
  const router = useRouter();
  const [isUploading, setIsUploading] = useState(false);
  const [result, setResult] = useState<{
    firms_created: number;
    contacts_created: number;
    errors: string[];
  } | null>(null);

  async function handleUpload(file: File) {
    setIsUploading(true);
    setResult(null);
    try {
      const data = await uploadFirmsCSV(file);
      setResult(data);
    } catch (e: any) {
      setResult({ firms_created: 0, contacts_created: 0, errors: [e.message] });
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Upload Firms & Contacts</h1>
        <p className="text-sm text-gray-500 mt-1">
          Upload a CSV or XLSX file with executive search firm contacts for Agent Suchi to
          reach out to.
        </p>
      </div>

      <CSVUploadZone onUpload={handleUpload} isUploading={isUploading} />

      {/* CSV Format Guide */}
      <div className="rounded-xl border border-gray-200 bg-white p-5">
        <h3 className="text-sm font-semibold text-gray-800 mb-3">Required CSV Format</h3>
        <div className="overflow-x-auto">
          <table className="text-xs text-gray-600">
            <thead>
              <tr className="border-b">
                <th className="px-2 py-1.5 text-left font-medium">Column</th>
                <th className="px-2 py-1.5 text-left font-medium">Required</th>
                <th className="px-2 py-1.5 text-left font-medium">Example</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              <tr><td className="px-2 py-1.5 font-mono">firm_name</td><td className="px-2 py-1.5 text-green-600">Yes</td><td className="px-2 py-1.5">Heidrick & Struggles</td></tr>
              <tr><td className="px-2 py-1.5 font-mono">contact_name</td><td className="px-2 py-1.5 text-green-600">Yes</td><td className="px-2 py-1.5">John Smith</td></tr>
              <tr><td className="px-2 py-1.5 font-mono">contact_email</td><td className="px-2 py-1.5 text-green-600">Yes</td><td className="px-2 py-1.5">john@firm.com</td></tr>
              <tr><td className="px-2 py-1.5 font-mono">contact_title</td><td className="px-2 py-1.5 text-gray-400">No</td><td className="px-2 py-1.5">Partner</td></tr>
              <tr><td className="px-2 py-1.5 font-mono">firm_website</td><td className="px-2 py-1.5 text-gray-400">No</td><td className="px-2 py-1.5">www.firm.com</td></tr>
              <tr><td className="px-2 py-1.5 font-mono">industry_focus</td><td className="px-2 py-1.5 text-gray-400">No</td><td className="px-2 py-1.5">Technology</td></tr>
              <tr><td className="px-2 py-1.5 font-mono">firm_location</td><td className="px-2 py-1.5 text-gray-400">No</td><td className="px-2 py-1.5">Mumbai</td></tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Upload Result */}
      {result && (
        <div
          className={`rounded-xl border p-5 ${
            result.errors.length > 0 && result.firms_created === 0
              ? "border-red-200 bg-red-50"
              : "border-green-200 bg-green-50"
          }`}
        >
          <h3 className="font-semibold text-gray-800">Upload Result</h3>
          <div className="mt-2 grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-500">Firms created:</span>{" "}
              <span className="font-bold text-gray-800">{result.firms_created}</span>
            </div>
            <div>
              <span className="text-gray-500">Contacts created:</span>{" "}
              <span className="font-bold text-gray-800">{result.contacts_created}</span>
            </div>
          </div>
          {result.errors.length > 0 && (
            <div className="mt-3">
              <p className="text-xs font-medium text-red-600 mb-1">
                Errors ({result.errors.length}):
              </p>
              <ul className="text-xs text-red-500 space-y-0.5 max-h-40 overflow-y-auto">
                {result.errors.map((err, i) => (
                  <li key={i}>• {err}</li>
                ))}
              </ul>
            </div>
          )}
          <button
            onClick={() => router.push("/outreach")}
            className="mt-4 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            View Firms Dashboard
          </button>
        </div>
      )}
    </div>
  );
}
