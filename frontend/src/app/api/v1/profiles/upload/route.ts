import { NextRequest, NextResponse } from "next/server";
import jwt from "jsonwebtoken";
import { randomUUID } from "crypto";
import pdfParse from "pdf-parse";

const JWT_SECRET = process.env.JWT_SECRET || "dev-secret-change-in-production";
const MAX_PDF_SIZE = 10 * 1024 * 1024; // 10MB

// In-memory storage for Phase-1 (replace with database later)
interface ProfileVersion {
  id: string;
  user_id: string;
  version: number;
  email: string;
  name?: string;
  phone?: string;
  location?: string;
  linkedin_url?: string;
  website_url?: string;
  headline?: string;
  summary?: string;
  experience: any[];
  education: any[];
  skills: string[];
  certifications: any[];
  languages: any[];
  created_at: Date;
}

const profiles = new Map<string, ProfileVersion[]>(); // user_id -> versions

function verifyToken(authHeader: string | null): { email: string } {
  if (!authHeader || !authHeader.startsWith("Bearer ")) {
    throw new Error("Invalid authorization header");
  }

  const token = authHeader.substring(7);
  try {
    const payload = jwt.verify(token, JWT_SECRET) as { email: string; exp?: number };
    if (!payload.email) {
      throw new Error("Invalid token payload");
    }
    return { email: payload.email };
  } catch (error: any) {
    if (error.name === "TokenExpiredError") {
      throw new Error("Token expired");
    }
    throw new Error("Invalid token");
  }
}

function extractBasicInfo(text: string): {
  name?: string;
  email?: string;
  phone?: string;
  location?: string;
  headline?: string;
  summary?: string;
  skills: string[];
  experience: any[];
  education: any[];
} {
  const lines = text.split("\n").map((l) => l.trim()).filter(Boolean);
  
  // Extract email
  const emailMatch = text.match(/\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/);
  const email = emailMatch ? emailMatch[0] : undefined;

  // Extract phone (various formats)
  const phoneMatch = text.match(/(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}/);
  const phone = phoneMatch ? phoneMatch[0] : undefined;

  // First non-empty line is often the name
  const name = lines[0] && !lines[0].includes("@") && !lines[0].match(/\d/) ? lines[0] : undefined;

  // Look for headline (often contains "|" or "at")
  let headline: string | undefined;
  for (const line of lines.slice(0, 10)) {
    if (line.includes("|") || line.includes("at ") || line.length > 30) {
      headline = line;
      break;
    }
  }

  // Extract skills (look for common skill keywords or bullet points)
  const skills: string[] = [];
  const skillKeywords = ["JavaScript", "Python", "React", "Node.js", "AWS", "Docker", "Kubernetes"];
  for (const keyword of skillKeywords) {
    if (text.toLowerCase().includes(keyword.toLowerCase())) {
      skills.push(keyword);
    }
  }

  // Simple experience extraction (look for dates and company names)
  const experience: any[] = [];
  const datePattern = /\d{4}|\w+\s+\d{4}/;
  for (let i = 0; i < lines.length - 2; i++) {
    if (datePattern.test(lines[i])) {
      const title = lines[i - 1] || "Unknown";
      const company = lines[i + 1] || "Unknown";
      experience.push({
        title,
        company,
        start_date: lines[i],
        end_date: "Present",
      });
    }
  }

  // Simple education extraction
  const education: any[] = [];
  const eduKeywords = ["University", "College", "Bachelor", "Master", "PhD", "Degree"];
  for (let i = 0; i < lines.length; i++) {
    if (eduKeywords.some((kw) => lines[i].includes(kw))) {
      education.push({
        school: lines[i],
        degree: lines[i + 1] || undefined,
      });
    }
  }

  // Summary is often a longer paragraph
  const summaryLines: string[] = [];
  for (const line of lines.slice(0, 20)) {
    if (line.length > 50 && !line.includes("@") && !datePattern.test(line)) {
      summaryLines.push(line);
    }
  }
  const summary = summaryLines.join(" ").substring(0, 500) || undefined;

  return {
    name,
    email,
    phone,
    location: undefined,
    headline,
    summary,
    skills,
    experience: experience.slice(0, 10),
    education: education.slice(0, 5),
  };
}

export async function POST(request: NextRequest) {
  try {
    // Verify authentication
    const authHeader = request.headers.get("authorization");
    const { email } = verifyToken(authHeader);

    // Get file from form data
    const formData = await request.formData();
    const file = formData.get("file") as File | null;

    if (!file) {
      return NextResponse.json({ detail: "No file provided" }, { status: 400 });
    }

    if (!file.name.toLowerCase().endsWith(".pdf")) {
      return NextResponse.json({ detail: "File must be a PDF" }, { status: 400 });
    }

    if (file.size > MAX_PDF_SIZE) {
      return NextResponse.json({ detail: "PDF exceeds 10MB limit" }, { status: 400 });
    }

    if (file.size === 0) {
      return NextResponse.json({ detail: "Empty file" }, { status: 400 });
    }

    // Read PDF
    const arrayBuffer = await file.arrayBuffer();
    const buffer = Buffer.from(arrayBuffer);

    // Parse PDF
    let pdfText: string;
    try {
      const pdfData = await pdfParse(buffer);
      pdfText = pdfData.text;
    } catch (parseError: any) {
      return NextResponse.json(
        { detail: `PDF parsing failed: ${parseError.message}` },
        { status: 400 }
      );
    }

    // Extract basic info
    const extracted = extractBasicInfo(pdfText);

    // Get or create user versions
    const userVersions = profiles.get(email) || [];
    const nextVersion = userVersions.length + 1;

    // Create profile version
    const profileVersion: ProfileVersion = {
      id: randomUUID(),
      user_id: email, // Using email as user_id for now
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
      created_at: new Date(),
    };

    // Mark all previous versions as not current (if we had that field)
    // For now, just add the new version
    userVersions.push(profileVersion);
    profiles.set(email, userVersions);

    // Return response matching ProfileUploadResponse schema
    return NextResponse.json({
      profile_version_id: profileVersion.id,
      version: profileVersion.version,
      name: profileVersion.name,
      email: profileVersion.email,
      phone: profileVersion.phone,
      location: profileVersion.location,
      linkedin_url: profileVersion.linkedin_url,
      website_url: profileVersion.website_url,
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
      created_at: profileVersion.created_at.toISOString(),
    });
  } catch (error: any) {
    if (error.message === "Invalid authorization header" || error.message === "Invalid token" || error.message === "Token expired") {
      return NextResponse.json({ detail: error.message }, { status: 401 });
    }
    return NextResponse.json(
      { detail: error.message || "Upload failed" },
      { status: 500 }
    );
  }
}
