"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import PdfUploadZone from "@/components/pdf-upload-zone";
import { uploadPdf, isAuthenticated } from "@/lib/api-client";
import { useEffect } from "react";

export default function UploadPage() {
  const router = useRouter();
  const [status, setStatus] = useState<"idle" | "uploading" | "done" | "error">("idle");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push("/");
    }
  }, []);

  async function handleUpload(file: File) {
    setStatus("uploading");
    setError(null);
    try {
      await uploadPdf(file);
      setStatus("done");
      setTimeout(() => router.push("/profile"), 1000);
    } catch (err: any) {
      setError(err.message || "Upload failed");
      setStatus("error");
    }
  }

  return (
    <div className="mx-auto max-w-lg space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">Upload LinkedIn PDF</h2>
      <p className="text-gray-600">
        Upload a new version of your LinkedIn profile. Previous versions are preserved.
      </p>

      {status === "idle" || status === "error" ? (
        <PdfUploadZone onFileSelect={handleUpload} />
      ) : status === "uploading" ? (
        <div className="flex flex-col items-center py-12 space-y-4">
          <div className="h-10 w-10 animate-spin rounded-full border-4 border-gray-200 border-t-primary-600" />
          <p className="text-gray-600">Parsing your profile...</p>
        </div>
      ) : (
        <div className="flex flex-col items-center py-12 space-y-2">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-green-100">
            <svg className="h-5 w-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <p className="text-gray-600">Profile updated! Redirecting...</p>
        </div>
      )}

      {error && (
        <div className="rounded-lg bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}
    </div>
  );
}
