"use client";
// Tells PostHog this visitor SAW the variant. The server chose it (lib/posthog-server.ts) but
// the server SDK's getAllFlags does not record exposure, and an experiment with no exposure
// events has no denominator. One getFeatureFlag call on mount sends $feature_flag_called with
// the variant the browser was bootstrapped with - the same one the server rendered.
import { useEffect } from "react";
import posthog from "posthog-js";

export function Exposure({ flag }: { flag: string }) {
  useEffect(() => {
    try {
      if (posthog.__loaded) posthog.getFeatureFlag(flag);
    } catch {
      // never block the page
    }
  }, [flag]);
  return null;
}
