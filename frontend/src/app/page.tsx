"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import PdfUploadZone from "@/components/pdf-upload-zone";
import { login, uploadPdf, isAuthenticated } from "@/lib/api-client";

export default function LandingPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [step, setStep] = useState<"email" | "upload" | "processing" | "done">("email");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isAuthenticated()) {
      router.push("/dashboard");
    }
  }, []);

  async function handleEmailSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await login(email);
      setStep("upload");
    } catch {
      setError("Failed to sign in. Please try again.");
    }
  }

  async function handleFileUpload(file: File) {
    setStep("processing");
    setError(null);
    try {
      await uploadPdf(file);
      setStep("done");
      setTimeout(() => router.push("/dashboard"), 1500);
    } catch (err: any) {
      setError(err.message || "Upload failed");
      setStep("upload");
    }
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center px-4">
      <div className="w-full max-w-md space-y-8">
        {/* Logo / Title */}
        <div className="text-center">
          <h1 className="text-4xl font-bold text-primary-900">Suchi</h1>
          <p className="mt-2 text-gray-600">
            Your autonomous job search agent
          </p>
        </div>

        {/* Step 1: Email */}
        {step === "email" && (
          <form onSubmit={handleEmailSubmit} className="space-y-4">
            <div>
              <label
                htmlFor="email"
                className="block text-sm font-medium text-gray-700"
              >
                Enter your email to get started
              </label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="mt-1 block w-full rounded-lg border border-gray-300 px-4 py-3 text-gray-900 placeholder-gray-400 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <button
              type="submit"
              className="w-full rounded-lg bg-primary-600 px-4 py-3 text-white font-medium hover:bg-primary-700 transition-colors"
            >
              Continue
            </button>
          </form>
        )}

        {/* Step 2: Upload */}
        {step === "upload" && (
          <div className="space-y-4">
            <p className="text-center text-sm text-gray-600">
              Upload your LinkedIn profile PDF
            </p>
            <PdfUploadZone onFileSelect={handleFileUpload} />
          </div>
        )}

        {/* Step 3: Processing */}
        {step === "processing" && (
          <div className="text-center space-y-4">
            <div className="mx-auto h-12 w-12 animate-spin rounded-full border-4 border-gray-200 border-t-primary-600" />
            <p className="text-gray-600">Parsing your profile...</p>
          </div>
        )}

        {/* Step 4: Done */}
        {step === "done" && (
          <div className="text-center space-y-2">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-green-100">
              <svg
                className="h-6 w-6 text-green-600"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 13l4 4L19 7"
                />
              </svg>
            </div>
            <p className="text-gray-600">
              Profile created! Redirecting...
            </p>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="rounded-lg bg-red-50 p-4 text-sm text-red-700">
            {error}
          </div>
        )}
      </div>
    </main>
  );
}
