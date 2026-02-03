import type { ProfileVersion } from "./store";

export function formatProfileResponse(p: ProfileVersion, isCurrent: boolean) {
  return {
    id: p.id,
    user_id: p.user_id,
    version: p.version,
    source_type: "linkedin_pdf",
    source_filename: null,
    headline: p.headline || null,
    summary: p.summary || null,
    experience: p.experience || [],
    education: p.education || [],
    skills: p.skills || [],
    certifications: p.certifications || [],
    languages: p.languages || [],
    patents: [],
    volunteer: [],
    publications: [],
    awards: [],
    projects: [],
    courses: [],
    pdf_storage_key: null,
    is_current: isCurrent,
    created_at: p.created_at,
    raw_parsed_data: {
      name: p.name || null,
      email: p.email || null,
      phone: p.phone || null,
      location: p.location || null,
      headline: p.headline || null,
      summary: p.summary || null,
      skill_categories: [],
    },
  };
}

export function formatVersionSummary(p: ProfileVersion, isCurrent: boolean) {
  return {
    id: p.id,
    version: p.version,
    source_type: "linkedin_pdf",
    source_filename: null,
    headline: p.headline || null,
    is_current: isCurrent,
    created_at: p.created_at,
  };
}
