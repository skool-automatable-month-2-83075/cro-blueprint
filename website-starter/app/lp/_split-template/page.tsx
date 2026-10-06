// ⛔ THE SPLIT-TEST TEMPLATE. /split-test copies this folder to app/lp/<slug>/ when a
// page enters a test. One URL, two pages, PostHog flips the coin.
//
//   VariantA.tsx  - the page you have today (the control). Moved here unchanged.
//   VariantB.tsx  - the challenger. Structurally different, not a button colour.
//   page.tsx      - this file. Renders whichever one PostHog put the visitor in.
//
// The flag key is `lp-<slug>`. It is created by code/split_test.py together with the
// experiment; until the flag exists every visitor sees VariantA, so copying this
// folder is safe before the test starts.
//
// Nothing else changes: the form, the call link, the events and the thank-you page are
// the same on both pages, so the only thing being measured is the page itself.
//
// Dev server only: ?preview=test or ?preview=control shows one page on demand so both can
// be scored and screenshotted before the flag exists. Ignored in production.
import type { Metadata } from "next";
import { Variant } from "@/components/lp/Variant";
import VariantA from "./VariantA";
import VariantB from "./VariantB";

export const metadata: Metadata = {
  title: "[Ad group service] in [Main city]",
  robots: { index: false, follow: false },
};

export const dynamic = "force-dynamic"; // the variant is decided per visitor, per request

export default async function Page({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const { preview } = await searchParams;
  return (
    <Variant
      flag="lp-[slug]"
      control={<VariantA />}
      test={<VariantB />}
      preview={typeof preview === "string" ? preview : undefined}
    />
  );
}
