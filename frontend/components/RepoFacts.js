import Section from "./Section";

const LANGUAGE_COLORS = ["bg-ink", "bg-vermilion", "bg-ochre", "bg-moss", "bg-ink-soft", "bg-rule"];

function Figure({ value, label }) {
  return (
    <div>
      <p className="font-display text-5xl font-light tabular-nums">{value.toLocaleString("en-US")}</p>
      <p className="mt-1 font-mono text-xs uppercase tracking-[0.18em] text-ink-soft">{label}</p>
    </div>
  );
}

function Languages({ languages }) {
  const entries = Object.entries(languages).sort((a, b) => b[1] - a[1]);
  const total = entries.reduce((sum, [, lines]) => sum + lines, 0);

  if (entries.length === 0) {
    return <p className="mt-10 text-sm text-ink-soft">No source code languages found.</p>;
  }

  return (
    <div className="mt-10">
      <div className="flex h-3 gap-0.5">
        {entries.map(([name, lines], index) => (
          <div key={name} className={LANGUAGE_COLORS[index % LANGUAGE_COLORS.length]} style={{ width: `${(lines / total) * 100}%` }} />
        ))}
      </div>
      <ul className="mt-5 grid gap-x-8 gap-y-2 font-mono text-sm sm:grid-cols-2">
        {entries.map(([name, lines], index) => (
          <li key={name} className="flex items-center gap-3">
            <span className={`h-2.5 w-2.5 ${LANGUAGE_COLORS[index % LANGUAGE_COLORS.length]}`} />
            <span className="flex-1">{name}</span>
            <span className="text-ink-soft">
              {lines.toLocaleString("en-US")} lines &middot; {Math.round((lines / total) * 100)}%
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function RepoFacts({ report }) {
  return (
    <Section number="01" title="Repository" note="What the Fetcher Agent found after cloning." delay={100}>
      <div className="flex gap-14">
        <Figure value={report.total_files} label="Files" />
        <Figure value={report.total_lines} label="Lines" />
      </div>
      <Languages languages={report.languages} />
    </Section>
  );
}
