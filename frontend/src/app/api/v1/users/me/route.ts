import { NextRequest, NextResponse } from "next/server";
import { verifyToken } from "../../_lib/auth";
import { getOrCreateUser } from "../../_lib/store";

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

    const user = getOrCreateUser(email);
    return NextResponse.json({
      id: user.id,
      email: user.email,
      name: user.name || null,
      phone: user.phone || null,
      location: user.location || null,
      linkedin_url: user.linkedin_url || null,
      created_at: user.created_at,
      updated_at: user.updated_at,
    });
  } catch (error: any) {
    return NextResponse.json({ detail: error.message || "Failed" }, { status: 500 });
  }
}
