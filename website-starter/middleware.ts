// Two jobs, both small.
//
// 1. Give every browser a stable visitor id (`ph_did`) so the server and PostHog
//    agree on which split-test variant this person is in. Set once, kept a year.
// 2. Production guard for the demo routes. /bold, /calm and /pick are design
//    templates for a FICTIONAL business - browsable on the dev server, never on a
//    live site: a reviewer finding a fake plumbing company on the domain reads as
//    a fake business. Never remove this.
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const DID_COOKIE = "ph_did";
const DEMO = /^\/(bold|calm)(\/|$)|^\/pick$/;

export function middleware(req: NextRequest) {
  if (process.env.NODE_ENV === "production" && DEMO.test(req.nextUrl.pathname)) {
    return NextResponse.rewrite(new URL("/__demo-route-blocked", req.url));
  }
  // The id has to exist on THIS request, not the next one. Setting it only on the response means
  // the first page view is rendered with no id, so the server cannot ask PostHog for a variant and
  // silently serves the control - the visitor is then bucketed on their second visit, if ever.
  // So: mint it, write it onto the request headers the page will read, and set the cookie back.
  let did = req.cookies.get(DID_COOKIE)?.value;
  const fresh = !did;
  if (!did) did = crypto.randomUUID();
  const headers = new Headers(req.headers);
  headers.set("x-ph-did", did);
  const res = NextResponse.next({ request: { headers } });
  if (fresh) {
    res.cookies.set(DID_COOKIE, did, { maxAge: 60 * 60 * 24 * 365, sameSite: "lax", path: "/" });
  }
  return res;
}

export const config = {
  // everything except Next internals and static files
  matcher: ["/((?!_next/|api/|_vercel|.*\\..*).*)"],
};
