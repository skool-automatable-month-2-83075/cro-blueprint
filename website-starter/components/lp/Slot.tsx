// A SLOT the owner fills (Jono, 28 September 2026: "use placeholders instead of random stuff... they
// fill in the thing, and if they don't have it, there's a fallback value").
//
//   filled  -> the real thing (children)
//   empty   -> visitors see the fallback, so the page can go live either way. A slot with no honest
//              fallback shows visitors NOTHING - never an empty play button, a blank logo row or a
//              stand-in face (those read as fake: 10 of 10 risk of losing them).
//
// On the dev server an empty slot is drawn the way the Claude Series kit draws one - a dashed frame
// with an icon and a label - so the owner sees exactly what to add and where. `devShows="fallback"`
// draws the fallback inside the dashed outline instead, for text slots where the wording is the point.
// Visitors never see a dashed frame or a label.
import type { CSSProperties, ReactNode } from "react";
import { Icon } from "@/components/kit/Icon";

const DEV = process.env.NODE_ENV !== "production";
/** True on the dev server, where empty slots are drawn. A section built only from slots checks this
 *  to decide whether to render at all when nothing is filled. */
export const SLOTS_VISIBLE = DEV;

export function Slot({ filled, label, hint, fallback, visitorsSee, devShows = "empty", onBlue = false, ratio = "16 / 9", icon = "image", children, style }: {
  filled: boolean; label: string; hint?: string; fallback?: ReactNode; visitorsSee?: string;
  devShows?: "empty" | "fallback"; onBlue?: boolean; ratio?: string; icon?: string; children?: ReactNode; style?: CSSProperties;
}) {
  if (filled) return <>{children}</>;
  if (!DEV) return <>{fallback ?? null}</>;
  if (devShows === "fallback" && fallback) {
    return (
      <div style={{ position: "relative", outline: `1.5px dashed ${onBlue ? "rgba(255,255,255,.7)" : "#b8bcc4"}`, outlineOffset: 8, borderRadius: 10, ...style }}>
        <Tag text={`Placeholder · ${label}`} hint={hint} />
        {fallback}
      </div>
    );
  }
  return <EmptySlot label={label} hint={hint} note={visitorsSee ? `Until it is filled, visitors see ${visitorsSee}.` : "Until it is filled, visitors see nothing here."} onBlue={onBlue} ratio={ratio} icon={icon} style={style} />;
}

function Tag({ text, hint }: { text: string; hint?: string }) {
  return (
    <span title={hint} style={{ position: "absolute", top: -12, right: 0, zIndex: 3, display: "inline-flex", alignItems: "center", padding: "4px 10px", borderRadius: 999,
      background: "#111214", color: "#fff", fontSize: 11, fontWeight: 600, letterSpacing: ".08em", textTransform: "uppercase", whiteSpace: "nowrap",
      maxWidth: "100%", overflow: "hidden", textOverflow: "ellipsis" }}>
      {text}
    </span>
  );
}

/** An empty slot on the dev server: the Claude Series placeholder frame. */
export function EmptySlot({ label, hint, note, onBlue = false, ratio = "16 / 9", icon = "image", style }: {
  label: string; hint?: string; note?: string; onBlue?: boolean; ratio?: string; icon?: string; style?: CSSProperties;
}) {
  const ink = onBlue ? "#ffffff" : "#1b1b1b";
  const soft = onBlue ? "rgba(255,255,255,.78)" : "#63666e";
  return (
    <div style={{ aspectRatio: ratio, minWidth: 0, overflow: "hidden", borderRadius: 4, display: "grid", placeItems: "center", padding: 24, textAlign: "center",
      border: `1px dashed ${onBlue ? "rgba(255,255,255,.55)" : "#8b8f98"}`, background: onBlue ? "rgba(255,255,255,.05)" : "#f4f5f7", ...style }}>
      <span style={{ display: "grid", gap: 8, justifyItems: "center", maxWidth: "38ch" }}>
        {icon && <Icon name={icon} size={24} color={soft} />}
        <strong style={{ fontSize: 14, fontWeight: 600, color: ink }}>{label}</strong>
        {hint && <span style={{ fontSize: 13, lineHeight: 1.45, color: soft }}>{hint}</span>}
        {note && <span style={{ fontSize: 12, lineHeight: 1.4, color: soft, fontStyle: "italic" }}>{note}</span>}
      </span>
    </div>
  );
}
