// Review badges, pre-built (Jono, 28 September 2026: "a beautiful looking Google review badge, Trustpilot
// badge, TrustIndex badge... pre-built so that people can load in their data and it just looks good").
//
//   <ReviewBadgeRow tone="dark" badges={[{ platform: "google", score: 4.9, count: 78 }, ...]} />
//
// Native, not pasted on: no card and no background, the text takes the colour of the section it sits in
// (tone "light" on white, "dark" on the brand blue), only the stars and the platform mark keep their
// own colours. They sit in ONE line: if only two fit the width, two show and the rest stay hidden,
// never a second row (Jono: "they should be in line... if only two fit then just show two").
//
// Drawn from the owner's real score and count - never a copied image and never a made-up number. With
// no score on file, pass null: empty stars and a dash, the dev-server preview of a slot. On an ad page a
// badge does not link out: a review profile is a fourth way off the page (blueprint, component 2).

export type ReviewPlatform = "google" | "trustpilot" | "trustindex";
export type BadgeData = { platform: ReviewPlatform; score: number | null; count: number | null };

const ROW_HEIGHT = 46;

function fmt(n: number) {
  return n.toLocaleString("en-US");
}

/** Five stars filled to the score, partial stars included. `boxed` is Trustpilot's white-on-green squares. */
function Stars({ score, color, size, boxed = false, empty }: { score: number | null; color: string; size: number; boxed?: boolean; empty: string }) {
  return (
    <span style={{ display: "inline-flex", gap: boxed ? 2 : 0 }} aria-hidden="true">
      {[0, 1, 2, 3, 4].map((i) => {
        const fill = score === null ? 0 : Math.max(0, Math.min(1, score - i));
        if (boxed) {
          return (
            <span key={i} style={{ position: "relative", width: size, height: size, background: empty, display: "grid", placeItems: "center", overflow: "hidden" }}>
              <span style={{ position: "absolute", inset: 0, width: `${fill * 100}%`, background: color }} />
              <span style={{ position: "relative", color: "#fff", fontSize: size * 0.8, lineHeight: 1 }}>★</span>
            </span>
          );
        }
        return (
          <span key={i} style={{ position: "relative", fontSize: size, lineHeight: 1, color: empty }}>
            ★<span style={{ position: "absolute", left: 0, top: 0, width: `${fill * 100}%`, overflow: "hidden", color }}>★</span>
          </span>
        );
      })}
    </span>
  );
}

function Mark({ platform }: { platform: ReviewPlatform }) {
  const box = { width: 30, height: 30, borderRadius: "50%", display: "grid", placeItems: "center", flex: "0 0 auto", background: "#fff" } as const;
  if (platform === "google") {
    return <span style={box}><span style={{ fontFamily: "Arial, sans-serif", fontWeight: 700, fontSize: 18, lineHeight: 1, color: "#4285F4" }}>G</span></span>;
  }
  if (platform === "trustpilot") {
    return <span style={{ ...box, background: "#00B67A" }}><span style={{ color: "#fff", fontSize: 17, lineHeight: 1 }}>★</span></span>;
  }
  return <span style={{ ...box, borderRadius: 8, background: "#1a8f4f" }}><span style={{ color: "#fff", fontSize: 15, fontWeight: 700, lineHeight: 1 }}>✓</span></span>;
}

const NAME: Record<ReviewPlatform, string> = { google: "Google", trustpilot: "Trustpilot", trustindex: "Trustindex" };

export function ReviewBadge({ platform, score, count, tone = "light" }: BadgeData & { tone?: "light" | "dark" }) {
  const ink = tone === "dark" ? "#ffffff" : "#111214";
  const soft = tone === "dark" ? "rgba(255,255,255,.78)" : "#63666e";
  const empty = tone === "dark" ? "rgba(255,255,255,.3)" : "#d9d9df";
  const scoreText = score === null ? "-" : score.toFixed(1);
  const countText = count === null ? "-" : fmt(count);
  const label = score === null ? `${NAME[platform]} rating, not filled in yet` : `${scoreText} out of 5 from ${countText} ${NAME[platform]} reviews`;
  return (
    <span role="img" aria-label={label} style={{ display: "inline-flex", alignItems: "center", gap: 10, height: ROW_HEIGHT, color: ink, whiteSpace: "nowrap",
      fontFamily: "system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif" }}>
      <Mark platform={platform} />
      <span style={{ display: "grid", gap: 3 }}>
        <span style={{ display: "inline-flex", alignItems: "center", gap: 7 }}>
          <strong style={{ fontSize: 16, lineHeight: 1, fontWeight: 700 }}>{scoreText}</strong>
          {platform === "trustpilot"
            ? <Stars score={score} color="#00B67A" size={15} boxed empty={empty} />
            : <Stars score={score} color={platform === "google" ? "#FBBC04" : "#F6BB06"} size={16} empty={empty} />}
        </span>
        <span style={{ fontSize: 12.5, lineHeight: 1, color: soft }}>
          <strong style={{ color: ink, fontWeight: 600 }}>{NAME[platform]}</strong> · {countText} reviews
        </span>
      </span>
    </span>
  );
}

/** One line of badges, a hairline between them. Whatever does not fit the width wraps to a second row,
 *  and the second row is cut off - so two show when only two fit, and nothing ever stacks. */
export function ReviewBadgeRow({ badges, tone = "light" }: { badges: BadgeData[]; tone?: "light" | "dark" }) {
  const rule = tone === "dark" ? "rgba(255,255,255,.28)" : "#dcdee3";
  return (
    <div data-badge-row="" style={{ display: "flex", flexWrap: "wrap", alignItems: "center", columnGap: 0, rowGap: 40, height: ROW_HEIGHT, overflow: "hidden" }}>
      {badges.map((b, i) => (
        <span key={b.platform} style={{ display: "inline-flex", paddingInline: i ? 22 : 0, paddingRight: 22, borderLeft: i ? `1px solid ${rule}` : "none" }}>
          <ReviewBadge {...b} tone={tone} />
        </span>
      ))}
    </div>
  );
}
