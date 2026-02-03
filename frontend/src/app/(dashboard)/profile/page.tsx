"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import VersionHistoryTable from "@/components/version-history-table";
import {
  getCurrentProfile,
  getProfileVersions,
  getProfileVersion,
  getMe,
  isAuthenticated,
} from "@/lib/api-client";
import type { ProfileVersion, ProfileVersionSummary, UserProfile } from "@/types/profile";

/* ── Chevron SVG ── */
function ChevronIcon({ open }: { open: boolean }) {
  return (
    <svg
      className={`h-5 w-5 shrink-0 transition-transform duration-200 ${open ? "rotate-180" : ""}`}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={2}
    >
      <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
    </svg>
  );
}

/* ── Accordion Section Wrapper ── */
function AccordionSection({
  title,
  count,
  open,
  onToggle,
  children,
}: {
  title: string;
  count?: number;
  open: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white overflow-hidden shadow-sm">
      <button
        onClick={onToggle}
        className="flex w-full items-center gap-3 px-5 py-3 text-left hover:bg-gray-50 transition-colors"
      >
        <span className="flex-1 text-sm font-bold uppercase tracking-wide text-gray-800">{title}</span>
        {count !== undefined && count > 0 && (
          <span className="rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-medium text-blue-700">
            {count}
          </span>
        )}
        <ChevronIcon open={open} />
      </button>
      {open && (
        <div className="border-t border-gray-100 px-5 py-4">
          {children}
        </div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════
   Ordered sections:
   1. HEADLINE (always visible banner)
   2. PROFESSIONAL SUMMARY
   3. KEY SKILLS AND ATTRIBUTES
   4. PROFESSIONAL EXPERIENCE
   5. TECHNICAL SKILLS
   6. EDUCATION
   7. PATENTS & PUBLICATIONS
   + any remaining LinkedIn sections
   ═══════════════════════════════════════════ */

export default function ProfilePage() {
  const router = useRouter();
  const [user, setUser] = useState<UserProfile | null>(null);
  const [profile, setProfile] = useState<ProfileVersion | null>(null);
  const [versions, setVersions] = useState<ProfileVersionSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeVersionId, setActiveVersionId] = useState<string | undefined>();

  const [openSections, setOpenSections] = useState<Record<string, boolean>>({});
  const [allExpanded, setAllExpanded] = useState(true);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push("/");
      return;
    }
    loadData();
  }, []);

  async function loadData() {
    try {
      const [userData, profileData, versionsData] = await Promise.all([
        getMe(),
        getCurrentProfile(),
        getProfileVersions(),
      ]);
      setUser(userData);
      setProfile(profileData);
      setVersions(versionsData.versions || []);
      if (profileData) {
        setActiveVersionId(profileData.id);
        doExpandAll(profileData);
      }
    } catch {
      // ok
    } finally {
      setLoading(false);
    }
  }

  function sectionKeysFor(p: ProfileVersion): string[] {
    const rpd = p.raw_parsed_data || {};
    const keys: string[] = [];
    // Contact first
    if (rpd.name || rpd.email || rpd.phone || rpd.location || rpd.linkedin_url) keys.push("contact");
    if (p.summary || rpd.summary) keys.push("summary");
    if (rpd.skill_categories?.length > 0) keys.push("key_skills");
    if (p.experience?.length > 0) keys.push("experience");
    if (p.skills?.length > 0) keys.push("technical_skills");
    if (p.education?.length > 0) keys.push("education");
    const hasPat = (p.patents?.length > 0) || (rpd.patents?.length > 0);
    const hasPub = p.publications?.length > 0;
    if (hasPat || hasPub) keys.push("patents_publications");
    if (p.certifications?.length > 0) keys.push("certifications");
    if (p.languages?.length > 0) keys.push("languages");
    if (p.volunteer?.length > 0) keys.push("volunteer");
    if (p.awards?.length > 0) keys.push("awards");
    if (p.projects?.length > 0) keys.push("projects");
    if (p.courses?.length > 0) keys.push("courses");
    return keys;
  }

  function doExpandAll(p: ProfileVersion) {
    const s: Record<string, boolean> = {};
    for (const k of sectionKeysFor(p)) s[k] = true;
    setOpenSections(s);
    setAllExpanded(true);
  }

  function doCollapseAll(p: ProfileVersion) {
    const s: Record<string, boolean> = {};
    for (const k of sectionKeysFor(p)) s[k] = false;
    setOpenSections(s);
    setAllExpanded(false);
  }

  async function handleViewVersion(versionId: string) {
    const data = await getProfileVersion(versionId);
    setProfile(data);
    setActiveVersionId(versionId);
    doExpandAll(data);
  }

  function toggle(key: string) {
    setOpenSections((prev) => {
      const next = { ...prev, [key]: !prev[key] };
      setAllExpanded(Object.values(next).every(Boolean));
      return next;
    });
  }

  function toggleAll() {
    if (!profile) return;
    if (allExpanded) doCollapseAll(profile);
    else doExpandAll(profile);
  }

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-200 border-t-blue-600" />
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="text-center py-20">
        <h2 className="text-xl font-semibold text-gray-900">No profile yet</h2>
        <p className="mt-2 text-gray-600">Upload your LinkedIn PDF to get started.</p>
        <button onClick={() => router.push("/upload")} className="mt-4 rounded-lg bg-blue-600 px-6 py-2 text-white hover:bg-blue-700">
          Upload PDF
        </button>
      </div>
    );
  }

  const parsed: any = profile.raw_parsed_data ?? {};
  const profileHeadline: string = profile.headline || parsed.headline || "";
  const profileSummary: string = profile.summary || parsed.summary || "";
  const categories: any[] = Array.isArray(parsed.skill_categories) ? parsed.skill_categories : [];
  const patents: any[] = Array.isArray(profile.patents) ? profile.patents : (Array.isArray(parsed.patents) ? parsed.patents : []);
  const publications: any[] = Array.isArray(profile.publications) ? profile.publications : [];

  // Contact fields
  const cName = parsed.name || (user ? user.name : "") || "";
  const cEmail = parsed.email || (user ? user.email : "") || "";
  const cPhone = parsed.phone || (user ? user.phone : "") || "";
  const cLocation = parsed.location || (user ? user.location : "") || "";
  const cLinkedin = parsed.linkedin_url || (user ? user.linkedin_url : "") || "";
  const cWebsite = parsed.website_url || "";

  // Debug log for troubleshooting
  console.log("[ProfilePage] profile keys:", Object.keys(profile));
  console.log("[ProfilePage] profile.headline:", profile.headline);
  console.log("[ProfilePage] profile.summary:", profile.summary);
  console.log("[ProfilePage] profileSummary:", profileSummary ? profileSummary.substring(0, 50) : "EMPTY");
  console.log("[ProfilePage] categories:", categories.length);
  console.log("[ProfilePage] cName:", cName, "cEmail:", cEmail);
  console.log("[ProfilePage] raw_parsed_data:", profile.raw_parsed_data ? "present" : "NULL");
  console.log("[ProfilePage] experience count:", profile.experience?.length);

  return (
    <div className="space-y-6">
      {/* ── Version History ── */}
      <div>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">Version History</h2>
          <button
            onClick={() => router.push("/upload")}
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700"
          >
            Upload New Version
          </button>
        </div>
        <VersionHistoryTable versions={versions} onView={handleViewVersion} activeVersionId={activeVersionId} />
      </div>

      {/* ── Profile Sections ── */}
      <div className="space-y-3">

        {/* ─── 1. HEADLINE (always visible, not collapsible) ─── */}
        <div className="rounded-lg bg-gradient-to-r from-slate-800 to-slate-900 px-6 py-5 text-white shadow-md">
          <div className="flex items-start justify-between gap-4">
            <div className="min-w-0 flex-1">
              <h2 className="text-2xl font-bold leading-tight">{cName || "—"}</h2>
              {profileHeadline ? (
                <p className="mt-2 text-base font-medium text-white/90 leading-relaxed">{profileHeadline}</p>
              ) : null}
            </div>
            <button
              onClick={toggleAll}
              className="shrink-0 rounded-md border border-white/20 px-3 py-1.5 text-xs font-medium text-white/80 hover:bg-white/10 transition-colors"
            >
              {allExpanded ? "Collapse All" : "Expand All"}
            </button>
          </div>
        </div>

        {/* ─── 2. CONTACT INFORMATION ─── */}
        {(cEmail || cPhone || cLocation || cLinkedin) ? (
          <AccordionSection title="Contact Information" open={openSections["contact"] ?? true} onToggle={() => toggle("contact")}>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {cEmail ? (
                <div className="rounded-lg bg-gray-50 p-3">
                  <p className="text-xs font-medium uppercase tracking-wider text-gray-400">Email</p>
                  <p className="mt-0.5 text-sm font-medium text-gray-900">{cEmail}</p>
                </div>
              ) : null}
              {cPhone ? (
                <div className="rounded-lg bg-gray-50 p-3">
                  <p className="text-xs font-medium uppercase tracking-wider text-gray-400">Phone</p>
                  <p className="mt-0.5 text-sm font-medium text-gray-900">{cPhone}</p>
                </div>
              ) : null}
              {cLocation ? (
                <div className="rounded-lg bg-gray-50 p-3">
                  <p className="text-xs font-medium uppercase tracking-wider text-gray-400">Location</p>
                  <p className="mt-0.5 text-sm font-medium text-gray-900">{cLocation}</p>
                </div>
              ) : null}
              {cLinkedin ? (
                <div className="rounded-lg bg-gray-50 p-3">
                  <p className="text-xs font-medium uppercase tracking-wider text-gray-400">LinkedIn</p>
                  <a href={cLinkedin} target="_blank" rel="noopener noreferrer" className="mt-0.5 text-sm text-blue-600 hover:underline break-all block">{cLinkedin}</a>
                </div>
              ) : null}
              {cWebsite ? (
                <div className="rounded-lg bg-gray-50 p-3">
                  <p className="text-xs font-medium uppercase tracking-wider text-gray-400">Website</p>
                  <a href={cWebsite} target="_blank" rel="noopener noreferrer" className="mt-0.5 text-sm text-blue-600 hover:underline break-all block">{cWebsite}</a>
                </div>
              ) : null}
            </div>
          </AccordionSection>
        ) : null}

        {/* ─── PROFESSIONAL SUMMARY ─── */}
        {profileSummary ? (
          <AccordionSection title="Professional Summary" open={openSections["summary"] ?? true} onToggle={() => toggle("summary")}>
            <p className="text-sm leading-relaxed text-gray-700 whitespace-pre-line">{profileSummary}</p>
          </AccordionSection>
        ) : null}

        {/* ─── KEY SKILLS & ATTRIBUTES ─── */}
        {categories.length > 0 ? (
          <AccordionSection
            title="Key Skills & Attributes"
            count={categories.reduce((n: number, c: any) => n + (Array.isArray(c.skills) ? c.skills.length : 0), 0)}
            open={openSections["key_skills"] ?? true}
            onToggle={() => toggle("key_skills")}
          >
            <div className="space-y-4">
              {categories.map((cat: any, i: number) => (
                <div key={i}>
                  <p className="mb-1.5 text-xs font-semibold uppercase tracking-wider text-gray-500">{cat.category}</p>
                  <div className="flex flex-wrap gap-2">
                    {(Array.isArray(cat.skills) ? cat.skills : []).map((s: string, j: number) => (
                      <span key={j} className="rounded-full bg-blue-50 px-3 py-1 text-xs font-medium text-blue-700 border border-blue-100">{s}</span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </AccordionSection>
        ) : null}

        {/* ─── PROFESSIONAL EXPERIENCE ─── */}
        {profile.experience?.length > 0 && (
          <AccordionSection
            title="Professional Experience"
            count={profile.experience.length}
            open={openSections["experience"] ?? true}
            onToggle={() => toggle("experience")}
          >
            <div className="space-y-6">
              {profile.experience.map((exp: any, i: number) => (
                <div key={i} className="relative pl-6 before:absolute before:left-0 before:top-1.5 before:h-2.5 before:w-2.5 before:rounded-full before:bg-blue-500 after:absolute after:left-[4.5px] after:top-5 after:h-[calc(100%-8px)] after:w-0.5 after:bg-gray-200 last:after:hidden">
                  <h4 className="font-semibold text-gray-900 leading-tight">{exp.title}</h4>
                  <p className="text-sm font-medium text-blue-600">{exp.company}</p>
                  <div className="flex flex-wrap gap-2 mt-0.5">
                    {exp.start_date && <span className="text-xs text-gray-500">{exp.start_date} – {exp.end_date || "Present"}</span>}
                    {exp.location && <span className="text-xs text-gray-500">&middot; {exp.location}</span>}
                  </div>
                  {exp.description && <div className="mt-2 text-sm text-gray-600 whitespace-pre-line leading-relaxed">{exp.description}</div>}
                </div>
              ))}
            </div>
          </AccordionSection>
        )}

        {/* 5. TECHNICAL SKILLS */}
        {profile.skills?.length > 0 && (
          <AccordionSection title="Technical Skills" count={profile.skills.length} open={openSections["technical_skills"] ?? true} onToggle={() => toggle("technical_skills")}>
            <div className="flex flex-wrap gap-2">
              {profile.skills.map((s: string, i: number) => (
                <span key={i} className="rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-700 border border-gray-200">{s}</span>
              ))}
            </div>
          </AccordionSection>
        )}

        {/* 6. EDUCATION */}
        {profile.education?.length > 0 && (
          <AccordionSection title="Education" count={profile.education.length} open={openSections["education"] ?? true} onToggle={() => toggle("education")}>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              {profile.education.map((edu: any, i: number) => (
                <div key={i} className="rounded-lg bg-gray-50 p-4">
                  <h4 className="font-semibold text-gray-900">{edu.school}</h4>
                  {edu.degree && <p className="text-sm text-gray-700">{edu.degree}{edu.field && ` in ${edu.field}`}</p>}
                  <div className="flex flex-wrap gap-2 mt-1">
                    {edu.start_date && <span className="text-xs text-gray-500">{edu.start_date} – {edu.end_date || ""}</span>}
                    {edu.location && <span className="text-xs text-gray-500">&middot; {edu.location}</span>}
                  </div>
                </div>
              ))}
            </div>
          </AccordionSection>
        )}

        {/* 7. PATENTS & PUBLICATIONS */}
        {(patents.length > 0 || publications.length > 0) && (
          <AccordionSection title="Patents & Publications" count={patents.length + publications.length} open={openSections["patents_publications"] ?? true} onToggle={() => toggle("patents_publications")}>
            <div className="space-y-4">
              {patents.length > 0 && (
                <div>
                  <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-gray-500">Patents</p>
                  <div className="space-y-3">
                    {patents.map((pat: any, i: number) => (
                      <div key={i} className="rounded-lg bg-gray-50 p-3">
                        <p className="font-medium text-gray-900 text-sm">{pat.title}</p>
                        {pat.patent_number && <p className="text-xs text-gray-500">{pat.patent_number}</p>}
                        {pat.date && <p className="text-xs text-gray-400">{pat.date}</p>}
                        {pat.description && <p className="mt-1 text-xs text-gray-600">{pat.description}</p>}
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {publications.length > 0 && (
                <div>
                  <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-gray-500">Publications</p>
                  <div className="space-y-3">
                    {publications.map((pub: any, i: number) => (
                      <div key={i} className="rounded-lg bg-gray-50 p-3">
                        <p className="font-medium text-gray-900 text-sm">{pub.title}</p>
                        {pub.publisher && <p className="text-xs text-gray-500">{pub.publisher}</p>}
                        {pub.date && <p className="text-xs text-gray-400">{pub.date}</p>}
                        {pub.description && <p className="mt-1 text-xs text-gray-600">{pub.description}</p>}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </AccordionSection>
        )}

        {/* ── Additional sections ── */}

        {profile.certifications?.length > 0 && (
          <AccordionSection title="Certifications" count={profile.certifications.length} open={openSections["certifications"] ?? true} onToggle={() => toggle("certifications")}>
            <div className="space-y-3">
              {profile.certifications.map((cert: any, i: number) => (
                <div key={i} className="rounded-lg bg-gray-50 p-3">
                  <p className="font-medium text-gray-900 text-sm">{cert.name}</p>
                  {cert.authority && <p className="text-xs text-gray-500">{cert.authority}</p>}
                  {cert.date && <p className="text-xs text-gray-400">{cert.date}</p>}
                </div>
              ))}
            </div>
          </AccordionSection>
        )}

        {profile.languages?.length > 0 && (
          <AccordionSection title="Languages" count={profile.languages.length} open={openSections["languages"] ?? true} onToggle={() => toggle("languages")}>
            <div className="flex flex-wrap gap-3">
              {profile.languages.map((lang: any, i: number) => (
                <div key={i} className="rounded-lg bg-gray-50 px-4 py-2.5">
                  <p className="font-medium text-gray-900 text-sm">{lang.language}</p>
                  {lang.proficiency && <p className="text-xs text-gray-500">{lang.proficiency}</p>}
                </div>
              ))}
            </div>
          </AccordionSection>
        )}

        {profile.volunteer?.length > 0 && (
          <AccordionSection title="Volunteer Experience" count={profile.volunteer.length} open={openSections["volunteer"] ?? true} onToggle={() => toggle("volunteer")}>
            <GenericList items={profile.volunteer} />
          </AccordionSection>
        )}

        {profile.awards?.length > 0 && (
          <AccordionSection title="Honors & Awards" count={profile.awards.length} open={openSections["awards"] ?? true} onToggle={() => toggle("awards")}>
            <GenericList items={profile.awards} />
          </AccordionSection>
        )}

        {profile.projects?.length > 0 && (
          <AccordionSection title="Projects" count={profile.projects.length} open={openSections["projects"] ?? true} onToggle={() => toggle("projects")}>
            <GenericList items={profile.projects} />
          </AccordionSection>
        )}

        {profile.courses?.length > 0 && (
          <AccordionSection title="Courses" count={profile.courses.length} open={openSections["courses"] ?? true} onToggle={() => toggle("courses")}>
            <GenericList items={profile.courses} />
          </AccordionSection>
        )}
      </div>
    </div>
  );
}

function GenericList({ items }: { items: any[] }) {
  return (
    <div className="space-y-3">
      {items.map((item, i) => (
        <div key={i} className="rounded-lg bg-gray-50 p-3">
          <p className="font-medium text-gray-900 text-sm">{item.title || item.role || item.name}</p>
          {(item.organization || item.publisher || item.issuer || item.institution) && (
            <p className="text-xs text-gray-500">{item.organization || item.publisher || item.issuer || item.institution}</p>
          )}
          {(item.date || item.start_date) && (
            <p className="text-xs text-gray-400">{item.start_date ? `${item.start_date} – ${item.end_date || "Present"}` : item.date}</p>
          )}
          {item.description && <p className="mt-1 text-xs text-gray-600 whitespace-pre-line">{item.description}</p>}
        </div>
      ))}
    </div>
  );
}
