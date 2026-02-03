import { NextRequest, NextResponse } from "next/server";
import jwt from "jsonwebtoken";
import { randomUUID } from "crypto";

// Simple in-memory user store for Phase-1 (replace with Vercel Postgres later)
const users = new Map<string, { email: string; id: string }>();

const JWT_SECRET = process.env.JWT_SECRET || "dev-secret-change-in-production";
const JWT_EXPIRY_HOURS = 24 * 7; // 1 week

export async function POST(request: NextRequest) {
  try {
    const { email } = await request.json();

    if (!email || typeof email !== "string") {
      return NextResponse.json(
        { detail: "Email is required" },
        { status: 400 }
      );
    }

    // Find or create user
    let user = users.get(email);
    if (!user) {
      user = {
        email,
        id: randomUUID(),
      };
      users.set(email, user);
    }

    // Create JWT token
    const exp = Math.floor(Date.now() / 1000) + JWT_EXPIRY_HOURS * 3600;
    const token = jwt.sign(
      { email: user.email, exp },
      JWT_SECRET,
      { algorithm: "HS256" }
    );

    return NextResponse.json({ access_token: token });
  } catch (error: any) {
    return NextResponse.json(
      { detail: error.message || "Login failed" },
      { status: 500 }
    );
  }
}
