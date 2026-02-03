import { NextRequest, NextResponse } from "next/server";
import { randomUUID } from "crypto";
import { verifyToken } from "../../_lib/auth";
import { getOrCreateUser, getProfilesForUser, saveProfileVersion } from "../../_lib/store";
import type { ProfileVersion } from "../../_lib/store";
// Import inner module directly to avoid pdf-parse's test file auto-loading
// when module.parent is null (common in serverless/bundled environments)
const pdfParse = require("pdf-parse/lib/pdf-parse.js");

const MAX_PDF_SIZE = 10 * 1024 * 1024; // 10MB

/**
 * LinkedIn PDF parser.
 *
 * LinkedIn "Save to PDF" files have a well-known structure:
 *   Contact → contact-info → Top Skills → skills → Languages → Honors-Awards →
 *   Publications → Patents → **Name** → **Headline (may span multiple lines)** →
 *   Location → Summary → summary text → Experience → jobs → Education → schools
 *
 * Each job block inside Experience:
 *   Company
 *   Title
 *   DateRange  (e.g. "October 2017 - October 2021 (4 years 1 month)")
 *   Location?
 *   Description lines…
 *
 * We also handle "Page X of Y" lines that LinkedIn inserts.
 */
function extractBasicInfo(text: string): any {
  const lines = text.split("\n").map((l) => l.trim()).filter(Boolean);

  // ── Remove "Page X of Y" noise ──
  const clean = lines.filter((l) => !/^Page\s+\d+\s+of\s+\d+$/i.test(l));

  // ── Locate well-known section anchors ──
  const idx = (keyword: string) => clean.findIndex((l) => l === keyword);

  const contactIdx = idx("Contact");
  const topSkillsIdx = idx("Top Skills");
  const languagesIdx = idx("Languages");
  const summaryIdx = idx("Summary");
  const experienceIdx = idx("Experience");
  const educationIdx = idx("Education");

  // ── Contact info (between "Contact" and "Top Skills" or next section) ──
  const emailMatch = text.match(/\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/);
  const phoneMatch = text.match(/(\+?\d[\d\s.()-]{7,}\d)/);
  const locationMatch = text.match(/(?:www\.linkedin\.com[^\n]*\n\s*\([^\)]*\)\s*\n\s*)([^\n]+)/);

  // ── Name & Headline ──
  // LinkedIn PDF structure before Summary:
  //   ... Patents content ... Name → Headline (multi-line, contains "|" or "at ") → Location → Summary
  // Strategy: walk backwards from "Summary" and identify the headline block (lines with "|"),
  // then the line just before headline is the name.
  let name: string | undefined;
  let headlineStartIdx = -1;

  const nameSearchEnd = summaryIdx > 0 ? summaryIdx : (experienceIdx > 0 ? experienceIdx : clean.length);

  if (nameSearchEnd > 0) {
    // Skip location line (last line before Summary, short, no "|")
    // Location typically contains a comma (e.g. "Bengaluru, Karnataka, India") or is a known city
    let headlineEndIdx = nameSearchEnd; // exclusive
    if (nameSearchEnd - 1 >= 0) {
      const lastLine = clean[nameSearchEnd - 1];
      if (lastLine && lastLine.length < 50 && !lastLine.includes("|") && (lastLine.includes(",") || lastLine.match(/^[A-Z][a-z]+$/))) {
        headlineEndIdx = nameSearchEnd - 1;
      }
    }

    // Strategy: scan the block before Summary/Location looking for the NAME line.
    // The name line is:  short (< 35 chars), looks like a person name (Title-cased words),
    //   no "|", no "@", no digits, no special chars, and is followed by headline lines.
    // Then everything between name and location is the headline.
    const isPersonName = (line: string): boolean => {
      if (line.length > 40 || line.length < 2) return false;
      if (line.includes("|") || line.includes("@") || line.includes("(") || line.includes(":")) return false;
      if (/\d/.test(line)) return false;
      // Should be 1-4 words, each starting with uppercase
      const words = line.split(/\s+/);
      if (words.length < 1 || words.length > 5) return false;
      return words.every(w => /^[A-Z]/.test(w));
    };

    // Search backwards from headlineEndIdx for the name
    for (let i = headlineEndIdx - 1; i >= Math.max(0, headlineEndIdx - 15); i--) {
      if (isPersonName(clean[i])) {
        // Verify the next line looks like a headline (has "|" or "at " or "@" or is long)
        if (i + 1 < headlineEndIdx) {
          const nextLine = clean[i + 1];
          if (nextLine && (nextLine.includes("|") || nextLine.includes(" at ") || nextLine.includes("@") || nextLine.length > 40)) {
            name = clean[i];
            headlineStartIdx = i + 1;
            break;
          }
        }
      }
    }
  }

  // ── Headline: lines from headlineStart up to (but not including) the location line ──
  let headline: string | undefined;
  // ── Location: line between headline and Summary (short, contains comma or is a city name) ──
  let location: string | undefined;

  // Determine where headline ends and location begins
  let headlineActualEnd = nameSearchEnd; // default: everything up to Summary
  if (summaryIdx > 0 && summaryIdx >= 2) {
    const lineBeforeSummary = clean[summaryIdx - 1];
    if (lineBeforeSummary && lineBeforeSummary.length < 50 && !lineBeforeSummary.includes("|") && (lineBeforeSummary.includes(",") || lineBeforeSummary.match(/^[A-Z][a-z]+$/))) {
      location = lineBeforeSummary;
      headlineActualEnd = summaryIdx - 1;
    }
  }

  if (headlineStartIdx > 0 && headlineStartIdx < headlineActualEnd) {
    const headlineLines: string[] = [];
    for (let i = headlineStartIdx; i < headlineActualEnd; i++) {
      headlineLines.push(clean[i]);
    }
    headline = headlineLines.join(" ").trim() || undefined;
  }

  // ── Top Skills from LinkedIn sidebar ──
  const sectionKeywords = ["Contact", "Top Skills", "Languages", "Honors-Awards", "Publications", "Patents", "Certifications", "Summary", "Experience", "Education"];
  const skills: string[] = [];
  if (topSkillsIdx >= 0) {
    const skillEnd = languagesIdx > topSkillsIdx ? languagesIdx : (topSkillsIdx + 10);
    for (let i = topSkillsIdx + 1; i < Math.min(skillEnd, clean.length); i++) {
      const line = clean[i];
      if (sectionKeywords.includes(line)) break;
      if (line.length < 50) skills.push(line);
    }
  }

  // ── Helper: reflow PDF text lines into paragraphs ──
  // PDF lines are ~60 chars wide; join continuation lines into flowing text
  // but preserve intentional paragraph breaks (bullet points, blank-line separators, headings)
  function reflowText(pdfLines: string[]): string {
    if (pdfLines.length === 0) return "";
    const result: string[] = [];
    let current = pdfLines[0];
    for (let i = 1; i < pdfLines.length; i++) {
      const line = pdfLines[i];
      // Start a new paragraph if line starts with a bullet/dash/number or is a heading-like line
      const isNewParagraph = /^[-–•▪■◦]/.test(line) || /^(\d+[\.\)]|\([a-z]\))/.test(line) ||
        (line.endsWith(":") && line.length < 60) || /^[A-Z][A-Z\s&]+:/.test(line) ||
        (line.startsWith(" ") && line.trim().length > 0);
      if (isNewParagraph) {
        result.push(current.trim());
        current = line;
      } else {
        current += " " + line;
      }
    }
    result.push(current.trim());
    return result.join("\n").trim();
  }

  // ── Summary ──
  let summary: string | undefined;
  if (summaryIdx >= 0) {
    const sumEnd = experienceIdx > summaryIdx ? experienceIdx : (summaryIdx + 40);
    const sumLines: string[] = [];
    for (let i = summaryIdx + 1; i < Math.min(sumEnd, clean.length); i++) {
      const line = clean[i];
      if (line === "Experience" || line === "Education") break;
      sumLines.push(line);
    }
    summary = reflowText(sumLines) || undefined;
  }

  // ── Experience ──
  const experience: any[] = [];
  // Date range pattern: "Month Year - Month Year (duration)" or "Year - Year (duration)"
  const dateRangePattern = /^(?:\w+\s+)?\d{4}\s*-\s*(?:\w+\s+)?\d{4}|^(?:\w+\s+)?\d{4}\s*-\s*Present/i;

  if (experienceIdx >= 0) {
    const expEnd = educationIdx > experienceIdx ? educationIdx : clean.length;
    let i = experienceIdx + 1;

    while (i < expEnd) {
      // Look for a date range line — this anchors a job entry
      if (dateRangePattern.test(clean[i])) {
        const dateLine = clean[i];
        // Title is the line before the date (or 2 lines before if company is between)
        // Company is 2 lines before date, Title is 1 line before date
        // Pattern: Company \n Title \n DateRange \n Location? \n Description...
        const title = i >= experienceIdx + 2 ? clean[i - 1] : "Unknown";
        const company = i >= experienceIdx + 3 ? clean[i - 2] : (i >= experienceIdx + 2 ? clean[i - 1] : "Unknown");

        // Parse start_date and end_date from dateLine
        const dateMatch = dateLine.match(/^(.+?)\s*-\s*([^(]+)/);
        const startDate = dateMatch ? dateMatch[1].trim() : dateLine;
        const endDate = dateMatch ? dateMatch[2].trim() : "Present";

        // Check if next line is a location (short, no date pattern)
        let loc: string | undefined;
        let descStart = i + 1;
        if (i + 1 < expEnd && clean[i + 1] && clean[i + 1].length < 50 && !dateRangePattern.test(clean[i + 1])) {
          // Could be location if it looks like a place
          const nextLine = clean[i + 1];
          if (nextLine.includes(",") || ["United States", "India", "Singapore", "Sweden", "Germany", "UK", "Canada"].some(c => nextLine.includes(c)) || /^[A-Z][a-z]/.test(nextLine)) {
            // Check it's not the next company name by seeing if line after is a title + date
            if (i + 3 < expEnd && dateRangePattern.test(clean[i + 3])) {
              // nextLine is likely the next company, not location
            } else {
              loc = nextLine;
              descStart = i + 2;
            }
          }
        }

        // Collect description lines until next job entry or section end
        const descLines: string[] = [];
        for (let j = descStart; j < expEnd; j++) {
          // Stop if we hit a line that's followed by a date range (next job's company or title)
          if (j + 1 < expEnd && dateRangePattern.test(clean[j + 1])) break; // This is the title of next job
          if (j + 2 < expEnd && dateRangePattern.test(clean[j + 2])) break; // This is the company of next job
          descLines.push(clean[j]);
        }

        experience.push({
          title: title !== company ? title : "Unknown",
          company,
          start_date: startDate,
          end_date: endDate,
          location: loc || undefined,
          description: reflowText(descLines) || undefined,
        });
      }
      i++;
    }
  }

  // ── Education ──
  const education: any[] = [];
  if (educationIdx >= 0) {
    // After "Education", lines are: School \n Degree/Field \n (optionally dates)
    let i = educationIdx + 1;
    while (i < clean.length) {
      const school = clean[i];
      if (!school) break;
      const degree = i + 1 < clean.length ? clean[i + 1] : undefined;
      education.push({ school, degree });
      i += 2; // Skip school + degree
      // Skip any additional lines (dates, etc.) until next school-like entry
      while (i < clean.length && clean[i] && /^\d{4}/.test(clean[i])) i++;
    }
  }

  return {
    name,
    email: emailMatch?.[0],
    phone: phoneMatch?.[0],
    location,
    headline,
    summary,
    skills,
    experience: experience.slice(0, 20),
    education: education.slice(0, 10),
  };
}

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function POST(request: NextRequest) {
  try {
    const authHeader = request.headers.get("authorization");
    if (!authHeader) {
      return NextResponse.json({ detail: "Authorization header required" }, { status: 401 });
    }

    let email: string;
    try {
      const result = verifyToken(authHeader);
      email = result.email;
    } catch (authError: any) {
      return NextResponse.json({ detail: authError.message || "Authentication failed" }, { status: 401 });
    }

    getOrCreateUser(email);

    const formData = await request.formData();
    const file = formData.get("file") as File | null;
    if (!file || !file.name.toLowerCase().endsWith(".pdf")) {
      return NextResponse.json({ detail: "File must be a PDF" }, { status: 400 });
    }
    if (file.size > MAX_PDF_SIZE || file.size === 0) {
      return NextResponse.json({ detail: file.size === 0 ? "Empty file" : "PDF exceeds 10MB limit" }, { status: 400 });
    }
    const arrayBuffer = await file.arrayBuffer();
    const buffer = Buffer.from(arrayBuffer);
    let pdfText: string;
    try {
      // pdf-parse might fail in serverless, wrap in try-catch with detailed error
      const pdfData = await pdfParse(buffer);
      pdfText = pdfData.text || "";
      if (!pdfText || pdfText.trim().length === 0) {
        return NextResponse.json({ detail: "PDF appears to be empty or unreadable" }, { status: 400 });
      }
    } catch (parseError: any) {
      console.error("PDF parse error:", parseError);
      // Return more detailed error for debugging
      const errorMsg = parseError.message || parseError.toString() || "Unknown parsing error";
      return NextResponse.json({ 
        detail: `PDF parsing failed: ${errorMsg}. File size: ${buffer.length} bytes` 
      }, { status: 400 });
    }
    const extracted = extractBasicInfo(pdfText);
    const existing = getProfilesForUser(email);
    const nextVersion = existing.length + 1;
    const profileVersion: ProfileVersion = {
      id: randomUUID(),
      user_id: email,
      version: nextVersion,
      email: extracted.email || email,
      name: extracted.name,
      phone: extracted.phone,
      location: extracted.location,
      headline: extracted.headline,
      summary: extracted.summary,
      experience: extracted.experience,
      education: extracted.education,
      skills: extracted.skills,
      certifications: [],
      languages: [],
      created_at: new Date().toISOString(),
    };
    saveProfileVersion(email, profileVersion);
    return NextResponse.json({
      profile_version_id: profileVersion.id,
      version: profileVersion.version,
      name: profileVersion.name,
      email: profileVersion.email,
      phone: profileVersion.phone,
      location: profileVersion.location,
      headline: profileVersion.headline,
      summary: profileVersion.summary,
      experience: profileVersion.experience,
      education: profileVersion.education,
      skills: profileVersion.skills,
      skill_categories: [],
      certifications: profileVersion.certifications,
      languages: profileVersion.languages,
      volunteer: [],
      patents: [],
      publications: [],
      awards: [],
      projects: [],
      courses: [],
      total_experience_years: null,
      created_at: profileVersion.created_at,
    });
  } catch (error: any) {
    console.error("Upload error:", error);
    if (error.message === "Invalid authorization header" || error.message === "Invalid token" || error.message === "Token expired") {
      return NextResponse.json({ detail: error.message }, { status: 401 });
    }
    const errorMessage = error.message || error.toString() || "Upload failed";
    return NextResponse.json({ detail: errorMessage }, { status: 500 });
  }
}
