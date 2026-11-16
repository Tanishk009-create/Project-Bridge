import {getToken} from "next-auth/jwt";
import {NextRequest, NextResponse} from "next/server";
export async function GET(request: NextRequest) {
  const base = process.env.NEXTAUTH_URL || request.nextUrl.origin;
  const token = await getToken({req: request, secret: process.env.NEXTAUTH_SECRET});
  if (!token?.googleIdToken || typeof token.googleIdToken !== "string") return NextResponse.redirect(new URL("/login?error=GoogleSession", base));
  try {
    const response = await fetch(`${process.env.BACKEND_URL || "http://127.0.0.1:8000"}/api/v1/auth/google`, {
      method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({id_token: token.googleIdToken}),
      cache: "no-store", signal: AbortSignal.timeout(15000),
    });
    if (!response.ok) return NextResponse.redirect(new URL(`/login?error=${response.status === 409 ? "AccountExists" : "GoogleSession"}`, base));
    const result = NextResponse.redirect(new URL("/home", base));
    for (const cookie of response.headers.getSetCookie()) result.headers.append("Set-Cookie", cookie);
    result.headers.set("Cache-Control", "no-store");
    return result;
  } catch { return NextResponse.redirect(new URL("/login?error=BackendUnavailable", base)); }
}
