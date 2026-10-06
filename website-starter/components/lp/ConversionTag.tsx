"use client";
// Fires the form conversion on /thank-you page load - never on a button click.
// /audit fills NEXT_PUBLIC_GADS_ID and NEXT_PUBLIC_GADS_FORM_LABEL in
// website/.env.local; until then this renders nothing and fires nothing.
import { useEffect } from "react";

declare global {
  interface Window { gtag?: (...args: unknown[]) => void; dataLayer?: unknown[] }
}

export function ConversionTag() {
  useEffect(() => {
    const adsId = process.env.NEXT_PUBLIC_GADS_ID;
    const label = process.env.NEXT_PUBLIC_GADS_FORM_LABEL;
    if (!window.gtag || !adsId || !label) return;
    // Fire ONCE per lead. React's dev-mode StrictMode runs this effect twice, and a refresh
    // of /thank-you would run it again - both showed as a second "Lead · Form Submit" in Tag
    // Assistant on 7 September 2026. The stash is per tab and survives a reload.
    const key = "lp_form_conversion_fired";
    try {
      if (window.sessionStorage.getItem(key)) return;
      window.sessionStorage.setItem(key, String(Date.now()));
    } catch { /* storage blocked: fall through and fire once for this effect */ }
    window.gtag("event", "conversion", { send_to: `${adsId}/${label}` });
    window.gtag("event", "generate_lead", { method: "landing_page_form" });
  }, []);
  return null;
}
