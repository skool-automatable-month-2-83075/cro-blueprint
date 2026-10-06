// The control: the page exactly as it was before the test. /split-test moves the
// existing app/lp/<slug>/page.tsx body here without changing a word of it.
export default function VariantA() {
  return <main>[the existing page, moved here unchanged]</main>;
}
