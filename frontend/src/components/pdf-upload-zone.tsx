"use client";

import { useCallback, useState, useRef } from "react";
import { cn } from "@/lib/utils";

interface PdfUploadZoneProps {
  onFileSelect: (file: File) => void;
}

export default function PdfUploadZone({ onFileSelect }: PdfUploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(
    (file: File) => {
      if (!file.name.toLowerCase().endsWith(".pdf")) {
        alert("Please upload a PDF file");
        return;
      }
      if (file.size > 10 * 1024 * 1024) {
        alert("File must be under 10MB");
        return;
      }
      setSelectedFile(file.name);
      onFileSelect(file);
    },
    [onFileSelect]
  );

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }

  function handleDragOver(e: React.DragEvent) {
    e.preventDefault();
    setIsDragging(true);
  }

  function handleDragLeave() {
    setIsDragging(false);
  }

  function handleInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  }

  return (
    <div
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onClick={() => inputRef.current?.click()}
      className={cn(
        "cursor-pointer rounded-xl border-2 border-dashed p-12 text-center transition-colors",
        isDragging
          ? "border-primary-500 bg-primary-50"
          : "border-gray-300 hover:border-primary-400 hover:bg-gray-50"
      )}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".pdf"
        onChange={handleInputChange}
        className="hidden"
      />

      <svg
        className="mx-auto h-12 w-12 text-gray-400"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
        />
      </svg>

      {selectedFile ? (
        <p className="mt-4 text-sm text-primary-600 font-medium">
          {selectedFile}
        </p>
      ) : (
        <>
          <p className="mt-4 text-sm text-gray-600">
            <span className="font-medium text-primary-600">
              Click to upload
            </span>{" "}
            or drag and drop
          </p>
          <p className="mt-1 text-xs text-gray-500">
            LinkedIn PDF only (max 10MB)
          </p>
        </>
      )}
    </div>
  );
}
