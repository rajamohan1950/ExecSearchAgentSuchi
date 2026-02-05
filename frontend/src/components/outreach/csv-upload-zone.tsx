"use client";

import { useCallback, useState } from "react";

interface CSVUploadZoneProps {
  onUpload: (file: File) => Promise<void>;
  isUploading: boolean;
}

export default function CSVUploadZone({ onUpload, isUploading }: CSVUploadZoneProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFile = useCallback(
    async (file: File) => {
      setError(null);
      const ext = file.name.toLowerCase().split(".").pop();
      if (!["csv", "xlsx", "xls"].includes(ext || "")) {
        setError("Please upload a .csv, .xlsx, or .xls file");
        return;
      }
      if (file.size > 10 * 1024 * 1024) {
        setError("File too large (max 10 MB)");
        return;
      }
      try {
        await onUpload(file);
      } catch (e: any) {
        setError(e.message || "Upload failed");
      }
    },
    [onUpload]
  );

  return (
    <div
      className={`relative rounded-xl border-2 border-dashed p-8 text-center transition-colors ${
        isDragOver
          ? "border-blue-400 bg-blue-50"
          : "border-gray-300 bg-white hover:border-gray-400"
      }`}
      onDragOver={(e) => {
        e.preventDefault();
        setIsDragOver(true);
      }}
      onDragLeave={() => setIsDragOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setIsDragOver(false);
        const file = e.dataTransfer.files[0];
        if (file) handleFile(file);
      }}
    >
      {isUploading ? (
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-200 border-t-blue-600" />
          <p className="text-sm text-gray-600">Processing upload...</p>
        </div>
      ) : (
        <div className="flex flex-col items-center gap-3">
          <div className="text-4xl">📋</div>
          <p className="text-sm font-medium text-gray-700">
            Drag & drop a CSV or XLSX file here
          </p>
          <p className="text-xs text-gray-500">
            Required columns: firm_name, contact_name, contact_email
          </p>
          <label className="mt-2 cursor-pointer rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors">
            Browse Files
            <input
              type="file"
              accept=".csv,.xlsx,.xls"
              className="hidden"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) handleFile(file);
              }}
            />
          </label>
        </div>
      )}

      {error && (
        <div className="mt-4 rounded-lg bg-red-50 px-4 py-2 text-sm text-red-700">
          {error}
        </div>
      )}
    </div>
  );
}
