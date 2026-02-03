import { NextRequest, NextResponse } from "next/server";
import jwt from "jsonwebtoken";
import { JWT_SECRET } from "../../_lib/auth";
import { getOrCreateUser } from "../../_lib/store";

const JWT_EXPIRY_HOURS = 24 * 7; // 1 week

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function POST(request: NextRequest) {
  try {
    const { email } = await request.json();

    if (!email || typeof email !== "string") {
      return NextResponse.json({ detail: "Email is required" }, { status: 400 });
    }

    getOrCreateUser(email);

    const exp = Math.floor(Date.now() / 1000) + JWT_EXPIRY_HOURS * 3600;
    const token = jwt.sign({ email, exp }, JWT_SECRET, { algorithm: "HS256" });

    return NextResponse.json({ access_token: token });
  } catch (error: any) {
    return NextResponse.json({ detail: error.message || "Login failed" }, { status: 500 });
  }
}
