import Section from "./Section";

export default function Suggestions({ suggestions }) {
  return (
    <Section number="04" title="What to fix" note="Rule suggestions first, then the AI's tips." delay={250}>
      {suggestions.length === 0 && <p className="text-ink-soft">Nothing to fix. Nicely done.</p>}
      <ol className="border-b border-rule">
        {suggestions.map((text, index) => (
          <li key={index} className="flex gap-5 border-t border-rule py-3.5">
            <span className="font-mono text-xs leading-6 text-vermilion">{String(index + 1).padStart(2, "0")}</span>
            <span className="text-lg leading-6">{text}</span>
          </li>
        ))}
      </ol>
    </Section>
  );
}
