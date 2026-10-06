"use client";
// Listens for the calendar embed on /thank-you confirming a booking and fires
// booking_made once. Covers Calendly's postMessage and the GoHighLevel embed's
// message shape; anything else shows up in the replay and gets added here.
// A booking is a SECONDARY signal: the lead already counted when the form was
// accepted. It is never a second lead.
import { useEffect } from "react";
import { EVENTS, track } from "@/lib/posthog";

export function BookingEvents() {
  useEffect(() => {
    track(EVENTS.thankYouViewed);
    let fired = false;
    const onMessage = (e: MessageEvent) => {
      if (fired) return;
      const d = e.data;
      // Calendly: origin calendly.com, {event: "calendly.event_scheduled"}
      const calendly = e.origin === "https://calendly.com" && d && typeof d === "object" && d.event === "calendly.event_scheduled";
      // GoHighLevel: origin api.leadconnectorhq.com, ["msgsndr-booking-complete", {...}] - verify in devtools once
      const ghl = /leadconnectorhq\.com$/.test(e.origin) && Array.isArray(d) && d[0] === "msgsndr-booking-complete";
      if (calendly || ghl) {
        fired = true;
        track(EVENTS.bookingMade, { provider: calendly ? "calendly" : "ghl", after_form: true, calendar_id: ghl ? d[1]?.calendarId : undefined });
      }
    };
    window.addEventListener("message", onMessage);
    return () => window.removeEventListener("message", onMessage);
  }, []);
  return null;
}
