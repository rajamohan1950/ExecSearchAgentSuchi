import { randomUUID } from "crypto";
import { readFileSync, writeFileSync, existsSync, mkdirSync } from "fs";
import { join } from "path";

export interface ProfileVersion {
  id: string;
  user_id: string;
  version: number;
  email: string;
  name?: string;
  phone?: string;
  location?: string;
  headline?: string;
  summary?: string;
  experience: any[];
  education: any[];
  skills: string[];
  certifications: any[];
  languages: any[];
  created_at: string;
}

export interface User {
  id: string;
  email: string;
  name?: string;
  phone?: string;
  location?: string;
  linkedin_url?: string;
  created_at: string;
  updated_at: string;
}

// File-based storage in /tmp — writable on Vercel, persists across warm invocations,
// and shared across all serverless functions in the same instance.
const STORE_DIR = join("/tmp", "suchi-store");
const PROFILES_FILE = join(STORE_DIR, "profiles.json");
const USERS_FILE = join(STORE_DIR, "users.json");

function ensureDir() {
  if (!existsSync(STORE_DIR)) {
    mkdirSync(STORE_DIR, { recursive: true });
  }
}

function loadJSON<T>(path: string, fallback: T): T {
  try {
    if (existsSync(path)) return JSON.parse(readFileSync(path, "utf-8"));
  } catch { /* corrupted — start fresh */ }
  return fallback;
}

function saveJSON(path: string, data: unknown) {
  ensureDir();
  writeFileSync(path, JSON.stringify(data), "utf-8");
}

export function getProfilesForUser(email: string): ProfileVersion[] {
  const all = loadJSON<Record<string, ProfileVersion[]>>(PROFILES_FILE, {});
  return all[email] || [];
}

export function saveProfileVersion(email: string, profile: ProfileVersion) {
  const all = loadJSON<Record<string, ProfileVersion[]>>(PROFILES_FILE, {});
  if (!all[email]) all[email] = [];
  all[email].push(profile);
  saveJSON(PROFILES_FILE, all);
}

export function getOrCreateUser(email: string): User {
  const all = loadJSON<Record<string, User>>(USERS_FILE, {});
  if (all[email]) return all[email];
  const now = new Date().toISOString();
  const user: User = { id: randomUUID(), email, created_at: now, updated_at: now };
  all[email] = user;
  saveJSON(USERS_FILE, all);
  return user;
}
