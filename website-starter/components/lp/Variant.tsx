// Render one of two pages at one URL, decided by a PostHog split-test flag.
//
//   <Variant flag="lp-drain-cleaning" control={<PageA />} test={<PageB />} />
//
// This is a SERVER component: the variant is chosen before any HTML leaves the
// server (lib/posthog-server.ts), so the visitor never sees A flash into B.
// The browser is bootstrapped with the same answer, so every event it sends
// carries `$feature/<flag>` and the experiment can read the result.
// Unknown flag, no PostHog key, or the flag is off -> control. A test that is
// not running shows the page you already had.
//
// The hidden marker is how code/check_tracking.py proves which page rendered, on the
// dev server and on the live URL. `hidden` means it has no box and no paint.
import type { ReactNode } from "react";
import { getVariant } from "@/lib/posthog-server";
import { Exposure } from "./Exposure";

export async function Variant({ flag, control, test, preview }: {
  flag: string; control: ReactNode; test: ReactNode;
  /** Dev server only: "test" or "control" forces one page so it can be scored and screenshotted
   *  before the flag exists (/lp/<slug>?preview=test). Ignored in production - the server and
   *  PostHog decide the variant there, never the URL. */
  preview?: string;
}) {
  const forced = process.env.NODE_ENV !== "production" && (preview === "test" || preview === "control") ? preview : undefined;
  const v = forced ?? (await getVariant(flag));
  return (
    <>
      <span hidden data-split-flag={flag} data-split-variant={v} data-split-forced={forced ? "true" : undefined} />
      <Exposure flag={flag} />
      {v === "test" ? test : control}
    </>
  );
}
