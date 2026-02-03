import { NextRequest, NextResponse } from "next/server";
import { verifyToken } from "../../../_lib/auth";
import { getProfilesForUser } from "../../../_lib/store";
import { formatProfileResponse } from "../../../_lib/format";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
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
    const version = all.find((v) => v.id === params.id);
    if (!version) {
      return NextResponse.json({ detail: "Version not found" }, { status: 404 });
    }

    const isCurrent = all[all.length - 1]?.id === version.id;
    return NextResponse.json(formatProfileResponse(version, isCurrent));
  } catch (error: any) {
    return NextResponse.json({ detail: error.message || "Failed" }, { status: 500 });
  }
}
