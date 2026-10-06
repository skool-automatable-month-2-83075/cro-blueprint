import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { site } from "@/lib/site.config";
import { captureServer, DID_COOKIE } from "@/lib/posthog-server";

// Every form on the site posts here; this forwards to the GHL inbound webhook.
// /audit collects the webhook up front and writes it into site.config.ts
// as `leadWebhook`. Until then, submissions return a clear error instead of
// vanishing - a lead disappearing silently is the worst failure a money page has.
//
// The same route takes the click-to-call beacon (JSON, event: "call_click") so
// one real number still tells you which keyword rang the phone.
//
// On success it records `lead_received` in PostHog from the SERVER. That is the
// count /analytics trusts: a refresh cannot double it and an ad blocker cannot hide it.

async function readBody(request: Request): Promise<Record<string, unknown>> {
  const type = request.headers.get("content-type") || "";
  if (type.includes("application/json")) return (await request.json()) as Record<string, unknown>;
  const form = await request.formData();
  return Object.fromEntries(form.entries());
}

export async function POST(request: Request) {
  console.log("[lead] in");
  const payload = await readBody(request);
  // A form with first and last name as two fields sends both; everything downstream keys on name.
  if (!(typeof payload.name === "string" && payload.name.trim()) && (payload.first_name || payload.last_name)) {
    payload.name = `${payload.first_name || ""} ${payload.last_name || ""}`.trim();
  }
  const isCall = payload.event === "call_click";
  // Every lead gets an id here, before anything else happens. GHL, PostHog and the CRM
  // reconciliation all key on it, so "58 in PostHog, 55 in GHL" becomes a list of three ids.
  const lead_id = crypto.randomUUID();
  // A check run submits a lead named TEST LEAD. It flows through like a real one and is tagged so no count includes it.
  const test_lead = typeof payload.name === "string" && /^test lead/i.test(payload.name);

  // The honeypot. A filled fax field is a bot: say thanks, send nothing.
  if (!isCall && typeof payload.company_fax === "string" && payload.company_fax.trim()) {
    return NextResponse.redirect(new URL("/thank-you", request.url), 303);
  }

  // LEAD_WEBHOOK_URL in website/.env.local wins; leadWebhook in lib/site.config.ts is the fallback.
  // The docs and /audit name both places, and this route read only the second (found 5 October 2026).
  const webhook = process.env.LEAD_WEBHOOK_URL || ((site as Record<string, unknown>).leadWebhook as string | null | undefined);
  if (!webhook || String(webhook).includes("TODO")) {
    return NextResponse.json(
      { ok: false, error: "Lead webhook not connected. Set LEAD_WEBHOOK_URL in website/.env.local, or leadWebhook in lib/site.config.ts." },
      { status: 503 },
    );
  }

  let res: Response;
  try {
    res = await fetch(webhook, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...payload, lead_id, test_lead, tags: test_lead ? "test-lead" : undefined,
        source: "website", page: payload.page ?? request.headers.get("referer") ?? "" }),
    });
  } catch (err) {
    console.log("[lead] webhook unreachable", (err as Error).message);
    return NextResponse.json({ ok: false, error: "Webhook unreachable" }, { status: 502 });
  }

  if (!res.ok) {
    console.log("[lead] webhook failed", res.status);
    return NextResponse.json({ ok: false, error: `Webhook responded ${res.status}` }, { status: 502 });
  }

  const did = (await cookies()).get(DID_COOKIE)?.value;
  const { name, phone, email, company_fax, first_name, last_name, ...safe } = payload as Record<string, string>; // never send PII to analytics
  void name; void phone; void email; void company_fax; void first_name; void last_name;
  await captureServer(isCall ? "call_click_received" : "lead_received", {
    ...safe, lead_id, test_lead, has_phone: Boolean(phone), has_email: Boolean(email),
  }, did);

  console.log("[lead] out", isCall ? "call" : "form");
  if (isCall) return NextResponse.json({ ok: true });
  return NextResponse.redirect(new URL("/thank-you", request.url), 303);
}
