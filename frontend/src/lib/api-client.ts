// Use relative URLs for Vercel (Next.js API routes), or external API if set
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("suchi_token");
}

export function setToken(token: string) {
  localStorage.setItem("suchi_token", token);
}

export function clearToken() {
  localStorage.removeItem("suchi_token");
}

export function isAuthenticated(): boolean {
  return !!getToken();
}

async function apiFetch(path: string, options: RequestInit = {}): Promise<Response> {
  const token = getToken();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const url = API_BASE ? `${API_BASE}${path}` : path;
  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    clearToken();
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
  }

  return response;
}

export async function login(email: string): Promise<{ access_token: string }> {
  const url = API_BASE ? `${API_BASE}/api/v1/auth/login` : "/api/v1/auth/login";
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
  if (!res.ok) throw new Error("Login failed");
  const data = await res.json();
  setToken(data.access_token);
  return data;
}

export async function uploadPdf(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  const token = getToken();
  const url = API_BASE ? `${API_BASE}/api/v1/profiles/upload` : "/api/v1/profiles/upload";
  const headers: Record<string, string> = {};
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  const res = await fetch(url, {
    method: "POST",
    headers,
    body: formData,
  });
  if (res.status === 401) {
    clearToken();
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
    throw new Error("Unauthorized");
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Upload failed" }));
    throw new Error(err.detail || "Upload failed");
  }
  return res.json();
}

export async function getCurrentProfile() {
  const res = await apiFetch("/api/v1/profiles/current");
  if (res.status === 404) return null;
  if (!res.ok) throw new Error("Failed to fetch profile");
  return res.json();
}

export async function getProfileVersions() {
  const res = await apiFetch("/api/v1/profiles/versions");
  if (!res.ok) throw new Error("Failed to fetch versions");
  return res.json();
}

export async function getProfileVersion(versionId: string) {
  const res = await apiFetch(`/api/v1/profiles/versions/${versionId}`);
  if (!res.ok) throw new Error("Failed to fetch version");
  return res.json();
}

export async function getMe() {
  const res = await apiFetch("/api/v1/users/me");
  if (!res.ok) throw new Error("Failed to fetch user");
  return res.json();
}

export async function getDashboardStats() {
  const res = await apiFetch("/api/v1/profiles/dashboard");
  if (!res.ok) throw new Error("Failed to fetch dashboard");
  return res.json();
}

// ── Outreach Agent APIs ──────────────────────────────────

export async function uploadFirmsCSV(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  const token = getToken();
  const url = API_BASE ? `${API_BASE}/api/v1/outreach/firms/bulk-upload` : "/api/v1/outreach/firms/bulk-upload";
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(url, { method: "POST", headers, body: formData });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Upload failed" }));
    throw new Error(err.detail || "Upload failed");
  }
  return res.json();
}

export async function getFirms(search?: string, status?: string) {
  const params = new URLSearchParams();
  if (search) params.set("search", search);
  if (status) params.set("status", status);
  const qs = params.toString();
  const res = await apiFetch(`/api/v1/outreach/firms${qs ? `?${qs}` : ""}`);
  if (!res.ok) throw new Error("Failed to fetch firms");
  return res.json();
}

export async function getFirmDetail(firmId: string) {
  const res = await apiFetch(`/api/v1/outreach/firms/${firmId}`);
  if (!res.ok) throw new Error("Failed to fetch firm");
  return res.json();
}

export async function getOutreachMetrics() {
  const res = await apiFetch("/api/v1/outreach/metrics/summary");
  if (!res.ok) throw new Error("Failed to fetch metrics");
  return res.json();
}

export async function getOutreachThreads() {
  const res = await apiFetch("/api/v1/outreach/threads");
  if (!res.ok) throw new Error("Failed to fetch threads");
  return res.json();
}

export async function getThreadMessages(threadId: string) {
  const res = await apiFetch(`/api/v1/outreach/threads/${threadId}`);
  if (!res.ok) throw new Error("Failed to fetch thread");
  return res.json();
}

export async function getAgentActions(limit = 50) {
  const res = await apiFetch(`/api/v1/outreach/metrics/actions?limit=${limit}`);
  if (!res.ok) throw new Error("Failed to fetch actions");
  return res.json();
}

export async function getAgentStatus() {
  const res = await apiFetch("/api/v1/outreach/agent-status");
  if (!res.ok) throw new Error("Failed to fetch agent status");
  return res.json();
}

export async function triggerOutreach(contactId: string) {
  const res = await apiFetch(`/api/v1/outreach/trigger/${contactId}`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to trigger outreach");
  return res.json();
}

export async function getDailyBriefings() {
  const res = await apiFetch("/api/v1/outreach/metrics/briefings");
  if (!res.ok) throw new Error("Failed to fetch briefings");
  return res.json();
}
