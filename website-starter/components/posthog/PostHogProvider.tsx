"use client";
// Boots posthog-js once, with the flags the server already evaluated for this
// visitor (see lib/posthog-server.ts). Bootstrapping is what stops a split test
// from flickering: the server rendered the right variant, and the browser agrees
// from its first frame instead of asking PostHog and repainting.
//
// Session replay is ON with every input masked - a phone number typed into a
// form must never be stored in a recording. Heatmaps, rage clicks and dead
// clicks are on so /analytics has something to read.
import { useEffect } from "react";
import posthog from "posthog-js";
import { PostHogProvider as Provider } from "posthog-js/react";

export type Bootstrap = { distinctID: string; featureFlags: Record<string, string | boolean> };

const KEY = process.env.NEXT_PUBLIC_POSTHOG_KEY;
const HOST = process.env.NEXT_PUBLIC_POSTHOG_HOST || "https://us.i.posthog.com";

function init(bootstrap?: Bootstrap) {
  if (!KEY || typeof window === "undefined" || posthog.__loaded) return;
  // The bootstrap is only honoured when it carries a distinctID. Without one, posthog-js mints its
  // own id, the server's flag answers are dropped, and every event goes out with no $feature/<key>
  // property - the experiment then has a denominator of zero. Found live 25 September 2026: 1 event
  // in 18 carried the variant. Never pass a bootstrap without its id.
  const boot = bootstrap && bootstrap.distinctID ? bootstrap : undefined;
  posthog.init(KEY, {
    // Straight to PostHog, no same-site proxy. A proxy is the documented way to survive ad
    // blockers, but BOTH ways of building one in Next broke the data here on 25 September 2026:
    // posthog-js gzips its POST bodies, a next.config rewrite corrupts them, and a route handler
    // stopped capture entirely. PostHog then answered {"flags":{}}, posthog-js overwrote the
    // server's bootstrap with that, and no event carried its $feature/<key> - an experiment with
    // no denominator. Correctness first: the direct host is verified working end to end.
    // To revisit a proxy: prove /flags/ still returns the flags AND events still arrive, with the
    // ten-visitor check in code/check_split.py, before shipping it.
    api_host: HOST,
    ui_host: HOST.replace(".i.posthog.com", ".posthog.com"),
    defaults: "2026-05-30",
    capture_pageview: "history_change",
    capture_pageleave: true,          // carries scroll depth for the heat map read
    autocapture: true,
    capture_dead_clicks: true,
    rageclick: true,
    enable_heatmaps: true,
    person_profiles: "identified_only",
    session_recording: {
      maskAllInputs: true,
      maskTextSelector: "[data-ph-mask]",
    },
    bootstrap: boot,
// The flags come from the server's bootstrap. posthog-js also re-fetches them from
    // /flags/ - that call must reach PostHog with its body intact, which is why the relay in
    // next.config.mjs forwards POST bodies rather than rewriting them (25 September 2026: a
    // plain rewrite corrupted the gzipped body, PostHog answered {"flags":{}}, and posthog-js
    // overwrote the bootstrap with it, so no event carried its variant).
    loaded: (ph) => {
      // Exposed for the tracking check and for a human in the console. Never used by the page.
      // ⛔ Never call identify() here: it clears the bootstrapped flags, so every event goes out
      // with no $feature/<key> and the experiment loses its denominator (found 25 September 2026).
      // The bootstrap's distinctID already pins the id; nothing else is needed.
      (window as unknown as { posthog: unknown }).posthog = ph;
    },
  });
}

export function PostHogProvider({ children, bootstrap }: { children: React.ReactNode; bootstrap?: Bootstrap }) {
  // Init synchronously on the client so flag reads during first render already have data.
  if (typeof window !== "undefined") init(bootstrap);
  useEffect(() => { init(bootstrap); }, [bootstrap]);
  return <Provider client={posthog}>{children}</Provider>;
}
