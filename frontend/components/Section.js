export default function Section({ number, title, note, delay = 0, children }) {
  return (
    <section className="reveal grid gap-6 border-t border-ink py-10 md:grid-cols-12" style={{ animationDelay: `${delay}ms` }}>
      <header className="md:col-span-3">
        <p className="font-mono text-xs text-vermilion">{number}</p>
        <h2 className="mt-1 font-display text-3xl font-medium tracking-tight">{title}</h2>
        {note && <p className="mt-2 text-sm text-ink-soft">{note}</p>}
      </header>
      <div className="md:col-span-9">{children}</div>
    </section>
  );
}
