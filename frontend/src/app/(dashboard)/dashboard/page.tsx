"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getDashboardStats, getMe, isAuthenticated } from "@/lib/api-client";
import type { UserProfile } from "@/types/profile";

interface DashboardStats {
  total_resumes_uploaded: number;
  days_since_last_update: number | null;
  current_version: number | null;
  total_experience_years: number | null;
  total_skills: number;
  total_roles: number;
  profile_completeness: number;
}

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<UserProfile | null>(null);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push("/");
      return;
    }
    loadData();
  }, []);

  async function loadData() {
    try {
      const [userData, statsData] = await Promise.all([
        getMe(),
        getDashboardStats(),
      ]);
      setUser(userData);
      setStats(statsData);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-200 border-t-blue-600" />
      </div>
    );
  }

  const hasProfile = stats && stats.total_resumes_uploaded > 0;

  return (
    <div className="space-y-8">
      {/* Welcome Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">
          Welcome back{user?.name ? `, ${user.name}` : ""}
        </h1>
        <p className="mt-1 text-gray-500">
          {hasProfile
            ? "Here's your profile overview"
            : "Upload your LinkedIn PDF to get started"}
        </p>
      </div>

      {!hasProfile ? (
        <div className="rounded-2xl border-2 border-dashed border-gray-300 bg-white p-12 text-center">
          <svg className="mx-auto h-16 w-16 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <h3 className="mt-4 text-lg font-semibold text-gray-900">No profile yet</h3>
          <p className="mt-2 text-gray-500">Upload your LinkedIn PDF to see your dashboard</p>
          <button
            onClick={() => router.push("/upload")}
            className="mt-6 rounded-lg bg-blue-600 px-6 py-3 text-white font-medium hover:bg-blue-700 transition-colors"
          >
            Upload LinkedIn PDF
          </button>
        </div>
      ) : (
        <>
          {/* Stats Grid */}
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
            <StatCard
              label="Resumes Uploaded"
              value={stats!.total_resumes_uploaded}
              icon={
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              }
              color="blue"
            />
            <StatCard
              label="Days Since Update"
              value={stats!.days_since_last_update ?? "-"}
              icon={
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              }
              color={
                stats!.days_since_last_update !== null && stats!.days_since_last_update > 30
                  ? "red"
                  : stats!.days_since_last_update !== null && stats!.days_since_last_update > 7
                  ? "yellow"
                  : "green"
              }
            />
            <StatCard
              label="Current Version"
              value={stats!.current_version ? `v${stats!.current_version}` : "-"}
              icon={
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                </svg>
              }
              color="purple"
            />
            <StatCard
              label="Experience"
              value={stats!.total_experience_years ? `${stats!.total_experience_years}+ yrs` : "-"}
              icon={
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              }
              color="indigo"
            />
            <StatCard
              label="Total Skills"
              value={stats!.total_skills}
              icon={
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              }
              color="teal"
            />
            <StatCard
              label="Total Roles"
              value={stats!.total_roles}
              icon={
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
              }
              color="orange"
            />
            <StatCard
              label="Profile Complete"
              value={`${stats!.profile_completeness}%`}
              icon={
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              }
              color={stats!.profile_completeness >= 80 ? "green" : stats!.profile_completeness >= 50 ? "yellow" : "red"}
            />
          </div>

          {/* Quick Actions */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <button
              onClick={() => router.push("/profile")}
              className="flex items-center gap-3 rounded-xl bg-white p-5 shadow-sm border border-gray-100 hover:shadow-md transition-shadow text-left"
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
              <div>
                <p className="font-medium text-gray-900">View Profile</p>
                <p className="text-xs text-gray-500">See parsed resume sections</p>
              </div>
            </button>
            <button
              onClick={() => router.push("/upload")}
              className="flex items-center gap-3 rounded-xl bg-white p-5 shadow-sm border border-gray-100 hover:shadow-md transition-shadow text-left"
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-green-50 text-green-600">
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                </svg>
              </div>
              <div>
                <p className="font-medium text-gray-900">Upload New Version</p>
                <p className="text-xs text-gray-500">Update your profile</p>
              </div>
            </button>
            <button
              onClick={() => router.push("/profile")}
              className="flex items-center gap-3 rounded-xl bg-white p-5 shadow-sm border border-gray-100 hover:shadow-md transition-shadow text-left"
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-purple-50 text-purple-600">
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <p className="font-medium text-gray-900">Version History</p>
                <p className="text-xs text-gray-500">Compare past versions</p>
              </div>
            </button>
          </div>
        </>
      )}
    </div>
  );
}

const colorMap: Record<string, { bg: string; text: string; iconBg: string }> = {
  blue: { bg: "bg-blue-50", text: "text-blue-700", iconBg: "bg-blue-100 text-blue-600" },
  green: { bg: "bg-green-50", text: "text-green-700", iconBg: "bg-green-100 text-green-600" },
  red: { bg: "bg-red-50", text: "text-red-700", iconBg: "bg-red-100 text-red-600" },
  yellow: { bg: "bg-amber-50", text: "text-amber-700", iconBg: "bg-amber-100 text-amber-600" },
  purple: { bg: "bg-purple-50", text: "text-purple-700", iconBg: "bg-purple-100 text-purple-600" },
  indigo: { bg: "bg-indigo-50", text: "text-indigo-700", iconBg: "bg-indigo-100 text-indigo-600" },
  teal: { bg: "bg-teal-50", text: "text-teal-700", iconBg: "bg-teal-100 text-teal-600" },
  orange: { bg: "bg-orange-50", text: "text-orange-700", iconBg: "bg-orange-100 text-orange-600" },
};

function StatCard({
  label,
  value,
  icon,
  color,
}: {
  label: string;
  value: string | number;
  icon: React.ReactNode;
  color: string;
}) {
  const colors = colorMap[color] || colorMap.blue;
  return (
    <div className={`rounded-xl ${colors.bg} p-5`}>
      <div className="flex items-center justify-between">
        <div className={`flex h-8 w-8 items-center justify-center rounded-lg ${colors.iconBg}`}>
          {icon}
        </div>
      </div>
      <p className={`mt-3 text-2xl font-bold ${colors.text}`}>{value}</p>
      <p className="mt-1 text-xs font-medium text-gray-600">{label}</p>
    </div>
  );
}
