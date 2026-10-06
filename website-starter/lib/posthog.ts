// The one place the page talks to PostHog from the browser.
//
// Every lead path on a page becomes ONE named event, sent from the moment the
// thing actually happened - the form's success callback, the tap on a tel: link -
// never from a page load. /analytics counts these; /split-test uses them as the goal.
// If PostHog is not loaded (no key yet, ad blocker, private mode) nothing throws
// and the page keeps working. Tracking never gets to break a money page.
import posthog from "posthog-js";

export const EVENTS = {
  formStarted: "lead_form_started",       // first focus on any field of the form
  fieldFocused: "form_field_focused",      // field: name
  fieldBlurred: "form_field_blurred",      // field: name · filled: true/false
  formSubmitted: "lead_form_submitted",    // the browser saw the webhook accept it
  formFailed: "lead_form_failed",          // the webhook did not accept it
  callClicked: "call_clicked",             // tap on a tel: link
  textClicked: "text_clicked",             // tap on an sms: link
  bookingMade: "booking_made",             // the calendar on /thank-you confirmed a slot
  thankYouViewed: "thank_you_viewed",      // reached /thank-you - a fallback, never the primary count
} as const;

export function track(event: string, props: Record<string, unknown> = {}, opts?: { beacon?: boolean }) {
  if (typeof window === "undefined") return;
  try {
    if (!posthog.__loaded) return;
    posthog.capture(event, { page: window.location.pathname, ...props },
      opts?.beacon ? { send_instantly: true, transport: "sendBeacon" } : undefined);
  } catch {
    // never block the visitor because analytics hiccuped
  }
}

/** Fire once per form per session, so a double click or a retry never counts twice. */
export function trackOnce(key: string, event: string, props: Record<string, unknown> = {}) {
  try {
    const k = `ph_once_${key}`;
    if (window.sessionStorage.getItem(k)) return;
    window.sessionStorage.setItem(k, "1");
  } catch {
    // storage blocked: fall through and send anyway
  }
  track(event, props);
}

/** The variant PostHog put this visitor in, for a given split-test flag. */
export function variantOf(flag: string): string | undefined {
  try {
    const v = posthog.getFeatureFlag(flag);
    return typeof v === "string" ? v : v ? "true" : undefined;
  } catch {
    return undefined;
  }
}
