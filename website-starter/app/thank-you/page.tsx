import type { Metadata } from "next";
import { site } from "@/lib/site.config";
import { BookingEvents } from "@/components/lp/BookingEvents";

// NEVER let this page be indexed. If it shows up in search results,
// people land here without converting and your conversion count becomes fiction.
export const metadata: Metadata = {
  title: "Thank you",
  description: "We've got your request.",
  robots: { index: false, follow: false },
  alternates: { canonical: "/thank-you" },
};

export default function ThankYou() {
  return (
    <div className="mx-auto max-w-2xl px-4 py-20 text-center">
      <BookingEvents />
      <h1 className="text-3xl font-bold">Got it - thanks.</h1>

      {/* THE most important line on this page. A specific time beats "soon" every time. */}
      <p className="mt-4 text-lg">
        We'll call you back <strong>within 30 minutes</strong> during business hours.
      </p>

      {/* The calendar lives HERE, never on the landing page. They book while they are warm. */}
      {site.bookingUrl ? (
        <div className="mt-10">
          <p className="mb-3 font-semibold">Pick a time that suits you</p>
          <iframe src={site.bookingUrl} title="Book a time" className="h-[700px] w-full rounded-lg border" />
        </div>
      ) : (
        <>
          <p className="mt-6 text-gray-600">Don't want to wait?</p>
          <a
            href={`tel:${site.phone.replace(/[^+\d]/g, "")}`}
            className="mt-2 inline-block rounded-lg bg-gray-900 px-6 py-3 font-semibold text-white"
          >
            Call {site.phone}
          </a>
        </>
      )}

      {/*
        The lead was counted when /api/lead accepted it (lead_received) and again in the
        browser (lead_form_submitted). This page only records thank_you_viewed - a
        fallback for /analytics to cross-check, never the number anyone quotes.
        Google Ads tag, if the Ads track is in use, still fires here on page load.
      */}
    </div>
  );
}
