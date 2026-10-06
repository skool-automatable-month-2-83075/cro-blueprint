// PostHog on the server: one visitor id per browser, flags evaluated once per
// request, and the exactly-once lead event.
//
// Why the server decides the variant: a page that renders variant A, then flips
// to B when the browser hears back from PostHog, has shown the visitor both
// pages. That is a broken test and a broken page. So middleware gives every
// browser a `ph_did` cookie, the server asks PostHog which variant that id is
// in, renders it, and hands the same answer to the browser as a bootstrap.
import "server-only";
import { cache } from "react";
import { cookies, headers } from "next/headers";
import { PostHog } from "posthog-node";

export const DID_COOKIE = "ph_did";
const KEY = process.env.NEXT_PUBLIC_POSTHOG_KEY;
const HOST = process.env.NEXT_PUBLIC_POSTHOG_HOST || "https://us.i.posthog.com";

let client: PostHog | null = null;
function ph(): PostHog | null {
  if (!KEY) return null;
  if (!client) client = new PostHog(KEY, { host: HOST, flushAt: 1, flushInterval: 0 });
  return client;
}

/** The visitor id middleware set. It arrives on the request header on the very first hit (before the
 *  cookie exists) and on the cookie thereafter, so a first-time visitor is bucketed on the page they
 *  actually landed on rather than silently served the control. */
export async function distinctId(): Promise<string> {
  const h = await headers();
  const fromHeader = h.get("x-ph-did");
  if (fromHeader) return fromHeader;
  const jar = await cookies();
  return jar.get(DID_COOKIE)?.value ?? "";
}

/** Every flag for this visitor, evaluated once per request. {} when PostHog is not configured. */
export const getFlags = cache(async (): Promise<Record<string, string | boolean>> => {
  const c = ph();
  const id = await distinctId();
  if (!c || !id) return {};
  try {
    const flags = await c.getAllFlags(id);
    return flags ?? {};
  } catch {
    return {};
  }
});

/** The variant key for one split-test flag: "control", "test", or "control" when unknown. */
export async function getVariant(flag: string): Promise<string> {
  const flags = await getFlags();
  const v = flags[flag];
  if (typeof v === "string") return v;
  return v ? "test" : "control";
}

/** What the browser needs to agree with the server from its first frame. */
export async function bootstrap() {
  return { distinctID: await distinctId(), featureFlags: await getFlags() };
}

/** An event for someone the browser never identified - a caller, a CRM record. `personKey` is a
 *  stable id for that human (a hashed phone number), and `uuid` makes the write idempotent, so a
 *  webhook retry or a second call from the same person does not become a second lead. */
export async function capturePerson(personKey: string, event: string, properties: Record<string, unknown>, uuid?: string) {
  const c = ph();
  if (!c) return;
  try {
    c.capture({ distinctId: personKey, event, properties, uuid });
    await c.flush();
  } catch {
    // tracking never fails a lead
  }
}

/** A server-side event, tied to the same visitor. Used by /api/lead for `lead_received`,
 *  the one count that cannot be faked by a refresh or blocked by an ad blocker.
 *
 *  It carries the visitor's split-test variants as `$feature/<key>`. Without them a server-side
 *  conversion lands with variant=None and the experiment cannot attribute it to either arm - the
 *  browser events would say a test is winning while the server count, the one that survives ad
 *  blockers, says nothing at all (found 25 September 2026 with call_click_received). */
export async function captureServer(event: string, properties: Record<string, unknown>, id?: string) {
  const c = ph();
  const did = id || (await distinctId());
  if (!c || !did) return;
  try {
    const flags = await getFlags();
    const tagged: Record<string, unknown> = { ...properties };
    for (const [key, value] of Object.entries(flags)) tagged[`$feature/${key}`] = value;
    if (Object.keys(flags).length) tagged["$active_feature_flags"] = Object.keys(flags);
    c.capture({ distinctId: did, event, properties: tagged });
    await c.flush();
  } catch {
    // tracking never fails a lead
  }
}
