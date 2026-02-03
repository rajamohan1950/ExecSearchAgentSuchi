import jwt from "jsonwebtoken";

export const JWT_SECRET = process.env.JWT_SECRET || "dev-secret-change-in-production";

export function verifyToken(authHeader: string | null): { email: string } {
  if (!authHeader || !authHeader.startsWith("Bearer ")) {
    throw new Error("Invalid authorization header");
  }
  const token = authHeader.substring(7);
  try {
    const payload = jwt.verify(token, JWT_SECRET) as { email: string };
    if (!payload.email) throw new Error("Invalid token payload");
    return { email: payload.email };
  } catch (error: any) {
    if (error.name === "TokenExpiredError") throw new Error("Token expired");
    throw new Error("Invalid token");
  }
}
