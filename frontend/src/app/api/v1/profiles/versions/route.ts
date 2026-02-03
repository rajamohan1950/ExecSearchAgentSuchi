import { NextRequest, NextResponse } from "next/server";
import { verifyToken } from "../../_lib/auth";
import { getProfilesForUser } from "../../_lib/store";
import { formatVersionSummary } from "../../_lib/format";

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
    // Return newest first so "Current" version is always at the top of the table
    const versions = all.map((p, i) => formatVersionSummary(p, i === all.length - 1)).reverse();
    return NextResponse.json({ versions });
  } catch (error: any) {
    return NextResponse.json({ detail: error.message || "Failed" }, { status: 500 });
  }
}
