// A preview of the pre-built review badges with example numbers, so an owner can see the finished look
// before loading their own. Dev server only: production answers 404, so the example numbers can never
// reach a visitor.
import { notFound } from "next/navigation";
import { ReviewBadgeRow, type BadgeData } from "@/components/lp/ReviewBadge";

export default function ReviewBadgesPreview() {
  if (process.env.NODE_ENV === "production") notFound();
  const filled: BadgeData[] = [
    { platform: "google", score: 4.9, count: 78 },
    { platform: "trustpilot", score: 4.6, count: 1234 },
    { platform: "trustindex", score: 4.8, count: 52 },
  ];
  const empty: BadgeData[] = filled.map((b) => ({ platform: b.platform, score: null, count: null }));
  const rows: { title: string; bg: string; color: string; tone: "light" | "dark" }[] = [
    { title: "On white", bg: "#f8f9fb", color: "#111214", tone: "light" },
    { title: "On the brand blue", bg: "#3b6ffd", color: "#ffffff", tone: "dark" },
  ];
  return (
    <main style={{ fontFamily: "system-ui, sans-serif", padding: 40, display: "grid", gap: 28 }}>
      <div>
        <h1 style={{ margin: 0, fontSize: 28 }}>Review badges</h1>
        <p style={{ margin: "8px 0 0", color: "#63666e" }}>
          Example numbers, for this preview only. On a page they come from the owner&rsquo;s real rating, set in proof.tsx.
        </p>
      </div>
      {rows.map((r) => (
        <section key={r.title} style={{ background: r.bg, color: r.color, padding: 32, borderRadius: 20, display: "grid", gap: 16 }}>
          <strong>{r.title}</strong>
          <ReviewBadgeRow badges={filled} tone={r.tone} />
          <strong>In a narrow column, only what fits one line shows</strong>
          <div style={{ maxWidth: 400 }}><ReviewBadgeRow badges={filled} tone={r.tone} /></div>
          <strong>Not filled in yet</strong>
          <ReviewBadgeRow badges={empty} tone={r.tone} />
        </section>
      ))}
    </main>
  );
}
