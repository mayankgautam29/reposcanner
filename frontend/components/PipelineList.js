const AGENTS = [
  { name: "Fetcher", job: "Clones the repo and counts files, lines and languages." },
  { name: "Rule Checker", job: "Hunts for leaked keys, missing files and long functions." },
  { name: "Router", job: "Sends easy work to a small model, hard code to a strong one." },
  { name: "AI Review", job: "Reads the README and main code like a human reviewer." },
  { name: "Validator", job: "A second model re-checks the review and gives a confidence." },
  { name: "AI Detector", job: "Estimates how much of the code an AI wrote." },
  { name: "Report", job: "Combines the scores into one report you can save." },
];

export default function PipelineList() {
  return (
    <div>
      <p className="font-mono text-xs uppercase tracking-[0.18em] text-ink-soft">The pipeline</p>
      <ol className="mt-4 border-b border-rule">
        {AGENTS.map((agent, index) => (
          <li key={agent.name} className="reveal flex gap-5 border-t border-rule py-3.5" style={{ animationDelay: `${300 + index * 90}ms` }}>
            <span className="font-mono text-xs leading-6 text-vermilion">{String(index + 1).padStart(2, "0")}</span>
            <div>
              <p className="font-display text-lg font-medium leading-6">{agent.name}</p>
              <p className="mt-0.5 text-sm text-ink-soft">{agent.job}</p>
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}
