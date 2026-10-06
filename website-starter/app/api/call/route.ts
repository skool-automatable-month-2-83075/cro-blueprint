import { NextResponse } from "next/server";
import { createHash } from "node:crypto";
import { capturePerson } from "@/lib/posthog-server";

// A phone call became a lead. GoHighLevel posts here when a call reaches the tracking number on
// the landing page; this records it in PostHog as `lead_call`, once per caller, forever.
//
// ⛔ WHAT COUNTS (Jono, 25 September 2026). Any inbound call GHL recognised. NOT "answered", and
// NOT "over 30 seconds". A missed call is still a lead - the business failed to pick up, the
// customer still raised their hand, and the number is in the CRM to call back. The old 30-second
// rule measured whether the business answered, not whether a lead arrived. `answered` and
// `duration_seconds` ride along as properties so the report can show the answer rate as its own
// number, which is a staffing problem, never a lead-count gate.
//
// ⛔ ONCE PER CALLER. The event's uuid is a hash of the caller's number, so a customer who rings
// five times is one lead however late the webhooks arrive or however often GHL retries.
//
// ⛔ WHICH VARIANT CALLED. GoHighLevel never saw the browser, so the only thing that can tell a
// call from the control apart from a call from the challenger is the NUMBER THEY DIALLED. Give
// each variant its own tracking number and map them here through CALL_NUMBER_MAP; the event then
// carries $feature/<flag> and the experiment counts calls per arm. With one number on both pages
// the map is empty, the variant is unknown, and calls are the page's total - a guardrail beside a
// test judged on form submissions. Never guess an arm from a number that serves both.
//
// The setup this expects, in GoHighLevel:
//   Settings > Phone numbers > buy one number per page, forward each to the real line
//   Automation > new workflow > trigger "Call Status" (or "Inbound Call") > no duration filter
//   Action > Webhook > POST to https://<your site>/api/call?secret=<CALL_WEBHOOK_SECRET>
//   Custom Data: one row, `phone` = the number they rang (the split-test number). GHL sends the caller's
//   own number as the contact's phone at the top level, so nothing else is needed.
//
// The honest limit: GHL shows one number to every visitor, so a call is attributed to the PAGE,
// never to a split-test arm. References/tracking-events.md says what dynamic number insertion
// would add. Do not read calls as a split-test metric on a static number.

type Body = Record<string, unknown>;

function pick(b: Body, ...keys: string[]) {
  for (const k of keys) {
    const v = b[k];
    if (typeof v === "string" && v.trim()) return v.trim();
    if (typeof v === "number") return String(v);
  }
  return "";
}

function digits(s: string) {
  return (s || "").replace(/\D/g, "");
}

/** The same phone number however it arrives: "+1 (555) 010-0123", "15550100123" and "5550100123" all
 *  match. North American numbers compare on their last ten digits; anything shorter compares whole. */
function sameNumber(a: string, b: string) {
  const x = digits(a), y = digits(b);
  if (!x || !y) return false;
  return x.length >= 10 && y.length >= 10 ? x.slice(-10) === y.slice(-10) : x === y;
}

export async function POST(request: Request) {
  console.log("[call] in");
  const secret = process.env.CALL_WEBHOOK_SECRET || "";
  const given = new URL(request.url).searchParams.get("secret") || request.headers.get("x-webhook-secret") || "";
  if (!secret || given !== secret) {
    console.error("[call] rejected: bad or missing secret");
    return NextResponse.json({ ok: false, error: "bad secret" }, { status: 401 });
  }

  let body: Body = {};
  try {
    body = (await request.json()) as Body;
  } catch {
    const form = await request.formData().catch(() => null);
    if (form) body = Object.fromEntries(form.entries());
  }

  // A GoHighLevel workflow webhook nests its custom rows under `customData`. Its `phone` is ALWAYS the
  // split-test number they rang (Jono, 29 September 2026: "that field holds the split test number rang"):
  // it tells page A from page B. The caller is GHL's own contact phone, which it adds at the top level.
  const custom = body.customData && typeof body.customData === "object" ? { ...(body.customData as Body) } : {};
  const dialled = pick(custom, "phone");
  delete custom.phone;
  body = { ...body, ...custom };
  console.log("[call] fields", Object.keys(body).join(","));   // the names only, never the values

  // A `to` in the URL is a fallback for a workflow that cannot send customData.
  const url = new URL(request.url);

  // GHL's field names differ by trigger and by the custom values a workflow sends, so read the
  // ones it actually uses and fall back through the aliases rather than trusting one shape.
  const from = digits(pick(body, "from", "caller", "callerNumber", "caller_number", "phone", "contact_phone", "fromNumber"));
  const to = digits(dialled || pick(body, "to", "toNumber", "called", "trackingNumber", "tracking_number") || url.searchParams.get("to") || "");
  const direction = pick(body, "direction", "callDirection", "call_direction") || "inbound";
  const status = pick(body, "status", "callStatus", "call_status", "disposition");
  const durationRaw = pick(body, "duration", "callDuration", "call_duration", "duration_seconds", "talkTime");
  const duration = Number(durationRaw) || 0;
  const callId = pick(body, "callId", "call_id", "id", "messageId", "conversationId");
  const contactId = pick(body, "contactId", "contact_id");
  let page = pick(body, "page", "landing_page", "source_page") || "";

  if (!from) {
    console.error("[call] rejected: no caller number in the payload");
    return NextResponse.json({ ok: false, error: "no caller number - map the caller's phone into the webhook body" }, { status: 400 });
  }
  if (direction && /out/i.test(direction)) {
    console.log("[call] ignored: outbound");
    return NextResponse.json({ ok: true, counted: false, reason: "outbound" });
  }

  // One lead per caller, forever. The same hash from a retry or a second call collapses in PostHog.
  const personKey = `caller:${from}`;
  const uuid = createHash("sha256").update(`lead_call:${from}`).digest("hex").slice(0, 32)
    .replace(/^(.{8})(.{4})(.{4})(.{4})(.{12})$/, "$1-$2-$3-$4-$5");

  // "no-answer" contains "answer", so the negatives are tested first. GHL uses no-answer, busy,
  // failed, canceled, voicemail; Twilio adds no-answer and busy verbatim.
  const missed = /no[-_ ]?answer|busy|fail|cancel|voicemail|missed|declin|reject|unanswered/i.test(status);
  // No status and no duration (a workflow sending the caller's phone alone): whether they got through is
  // unknown, so it is recorded as unknown, never as a missed call.
  const told = !!status || durationRaw !== "";
  const answered = told ? !missed && (/answer|complet|success|in[-_ ]?progress/i.test(status) || duration > 0) : null;

  // CALL_NUMBER_MAP: "<digits>=<flag>:<variant>,<digits>=<flag>:<variant>" - one entry per tracking
  // number under test. /split-test writes it when two numbers are given.
  const variantProps: Record<string, unknown> = {};
  let variantLabel = "";
  for (const entry of (process.env.CALL_NUMBER_MAP || "").split(",")) {
    const [num, target] = entry.split("=").map((x) => (x || "").trim());
    if (!num || !target || !sameNumber(num, to)) continue;
    const [flag, variant] = target.split(":").map((x) => (x || "").trim());
    if (!flag || !variant) continue;
    // GoHighLevel never saw the page, but the number knows it: flag lp-<slug> is the page /lp/<slug>.
    if (!page && flag.startsWith("lp-")) page = `/lp/${flag.slice(3)}`;
    variantProps[`$feature/${flag}`] = variant;
    variantProps.$active_feature_flags = [flag];
    variantLabel = `${flag}=${variant}`;
  }
  await capturePerson(personKey, "lead_call", {
    page: page || "/",
    answered,                       // reported, never a gate: a missed call is still a lead
    duration_seconds: duration,
    call_status: status || "unknown",
    tracking_number: to,
    ghl_call_id: callId,
    ghl_contact_id: contactId,
    source: "ghl",
    ...variantProps,
    $set_once: { lead_first_channel: "call", first_call_at: new Date().toISOString() },
  }, uuid);

  console.log("[call] out", answered === null ? "unknown" : answered ? "answered" : "missed", duration + "s", variantLabel || "no variant (one number serves both arms)");
  return NextResponse.json({ ok: true, counted: true, answered, duration_seconds: duration, variant: variantLabel || null });
}
