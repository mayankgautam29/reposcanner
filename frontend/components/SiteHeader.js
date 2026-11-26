export default function SiteHeader() {
  return (
    <header className="mx-auto flex max-w-6xl items-baseline justify-between border-b border-ink px-5 py-5 sm:px-8">
      <span className="font-display text-2xl font-semibold tracking-tight">RepoScan</span>
      <span className="hidden font-mono text-xs text-ink-soft sm:block">rules + Gemini + a second opinion</span>
    </header>
  );
}
