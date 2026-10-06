"use client";
// One listener for the whole page. Drop it once in the page and every lead path
// is measured without touching each button:
//   - a tap on any tel: link      -> call_clicked  (source = data-source or the nearest section id)
//   - a tap on any sms: link      -> text_clicked
//   - first focus on a form field -> lead_form_started
//   - every field focus / blur    -> form_field_focused / form_field_blurred (filled: true/false)
// That last pair is what turns "the form is cold" into "30 people died on the address field".
// Field VALUES are never sent - only the field name and whether it was left filled.
import { useEffect } from "react";
import { EVENTS, track } from "@/lib/posthog";

function sourceOf(el: Element): string {
  const tagged = el.closest<HTMLElement>("[data-source]")?.dataset.source;
  if (tagged) return tagged;
  const sec = el.closest("section[id], [data-section]") as HTMLElement | null;
  return sec?.id || sec?.dataset.section || "page";
}

export function LeadEvents({ form = "lead" }: { form?: string }) {
  useEffect(() => {
    let started = false;
    const onClick = (e: MouseEvent) => {
      const a = (e.target as Element | null)?.closest?.("a[href]") as HTMLAnchorElement | null;
      if (!a) return;
      const href = a.getAttribute("href") || "";
      if (/^tel:/i.test(href)) track(EVENTS.callClicked, { source: sourceOf(a), form }, { beacon: true });
      else if (/^sms:/i.test(href)) track(EVENTS.textClicked, { source: sourceOf(a), form }, { beacon: true });
    };
    const fieldOf = (t: EventTarget | null) => {
      const el = t as HTMLElement | null;
      if (!el || !("name" in el)) return null;
      const f = el as HTMLInputElement;
      if (!f.form || f.type === "hidden" || f.tabIndex === -1) return null;
      return f;
    };
    const onFocus = (e: FocusEvent) => {
      const f = fieldOf(e.target); if (!f) return;
      if (!started) { started = true; track(EVENTS.formStarted, { form }); }
      track(EVENTS.fieldFocused, { form, field: f.name });
    };
    const onBlur = (e: FocusEvent) => {
      const f = fieldOf(e.target); if (!f) return;
      const filled = f.type === "checkbox" || f.type === "radio" ? f.checked : Boolean(f.value?.trim());
      track(EVENTS.fieldBlurred, { form, field: f.name, filled });
    };
    document.addEventListener("click", onClick, true);
    document.addEventListener("focusin", onFocus);
    document.addEventListener("focusout", onBlur);
    return () => {
      document.removeEventListener("click", onClick, true);
      document.removeEventListener("focusin", onFocus);
      document.removeEventListener("focusout", onBlur);
    };
  }, [form]);
  return null;
}
