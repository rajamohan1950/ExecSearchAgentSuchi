import { NextRequest, NextResponse } from "next/server";
import { verifyToken } from "../../_lib/auth";
import { getProfilesForUser } from "../../_lib/store";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(request: NextRequest) {
  try {
    const authHeader = request.headers.get("authorization");
    if (!authHeader) {
      return NextResponse.json({ detail: "Authorization header required" }, { status: 401 });
    }

    let email: string;
    try {
      email = verifyToken(authHeader).email;
    } catch (e: any) {
      return NextResponse.json({ detail: e.message }, { status: 401 });
    }

    const all = getProfilesForUser(email);
    const latest = all.length > 0 ? all[all.length - 1] : null;

    let daysSinceLastUpdate: number | null = null;
    if (latest) {
      daysSinceLastUpdate = Math.floor((Date.now() - new Date(latest.created_at).getTime()) / (1000 * 60 * 60 * 24));
    }

    let filledSections = 0;
    const totalSections = 7;
    if (latest) {
      if (latest.name) filledSections++;
      if (latest.headline) filledSections++;
      if (latest.summary) filledSections++;
      if (latest.experience.length > 0) filledSections++;
      if (latest.education.length > 0) filledSections++;
      if (latest.skills.length > 0) filledSections++;
      if (latest.certifications.length > 0) filledSections++;
    }

    return NextResponse.json({
      total_resumes_uploaded: all.length,
      days_since_last_update: daysSinceLastUpdate,
      current_version: latest ? latest.version : null,
      total_experience_years: null,
      total_skills: latest ? latest.skills.length : 0,
      total_roles: latest ? latest.experience.length : 0,
      profile_completeness: Math.round((filledSections / totalSections) * 100),
    });
  } catch (error: any) {
    return NextResponse.json({ detail: error.message || "Failed" }, { status: 500 });
  }
}
