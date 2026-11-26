import Section from "./Section";

export default function AgentLog({ log }) {
  return (
    <Section number="05" title="Agent log" note="Exactly what each agent did, in order." delay={300}>
      <ol className="ml-1.5 border-l border-ink">
        {log.map((step, index) => (
          <li key={index} className="relative pb-6 pl-8 last:pb-0">
            <span className="absolute -left-[5px] top-1.5 h-2.5 w-2.5 bg-ink" />
            <p className="font-mono text-xs uppercase tracking-[0.18em] text-vermilion">{step.agent}</p>
            <p className="mt-1">{step.message}</p>
          </li>
        ))}
      </ol>
    </Section>
  );
}
