import { NextRequest, NextResponse } from "next/server";
import { verifyToken } from "../../_lib/auth";
import { getProfilesForUser } from "../../_lib/store";
import { formatProfileResponse } from "../../_lib/format";

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

    const versions = getProfilesForUser(email);
    if (versions.length === 0) {
      return NextResponse.json({ detail: "No profile found" }, { status: 404 });
    }

    return NextResponse.json(formatProfileResponse(versions[versions.length - 1], true));
  } catch (error: any) {
    return NextResponse.json({ detail: error.message || "Failed" }, { status: 500 });
  }
}
