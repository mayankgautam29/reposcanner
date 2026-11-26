import Section from "./Section";
import SubHeading from "./SubHeading";

function Stamp({ label, value, color }) {
  return (
    <div className={`stamp inline-block shrink-0 border-2 px-5 py-3 text-center font-mono uppercase tracking-[0.2em] ${color}`}>
      <p className="text-xs">{label}</p>
      <p className="mt-1 font-display text-3xl tracking-normal">{value}</p>
    </div>
  );
}

function ModelLine({ ai }) {
  return (
    <p className="mt-10 font-mono text-xs text-ink-soft">
      README: {ai.models.readme} &middot; Review: {ai.models.review} &middot; Validator: {ai.models.validator} &middot; {ai.tries}{" "}
      {ai.tries === 1 ? "try" : "tries"}
    </p>
  );
}

function Wrapper({ children }) {
  return (
    <Section number="03" title="AI review" note="A model reads the code, a second model checks it." delay={200}>
      {children}
    </Section>
  );
}

export default function AiReview({ report }) {
  const ai = report.ai;

  if (ai.status === "skipped") {
    return (
      <Wrapper>
        <p className="text-ink-soft">No source code was found, so the AI review was skipped.</p>
      </Wrapper>
    );
  }

  if (ai.status === "not_sure") {
    return (
      <Wrapper>
        <div className="flex flex-wrap items-start gap-8">
          <Stamp label="Not sure" value={`${ai.confidence}/100`} color="border-vermilion text-vermilion" />
          <p className="min-w-60 flex-1 font-display text-2xl leading-snug">
            The validator did not trust the review, even after {ai.tries} tries, so it is not shown. The final score uses the rule
            score only.
          </p>
        </div>
        <p className="mt-6 text-sm italic text-ink-soft">Validator said: {ai.confidence_reason}</p>
        <SubHeading>README in short</SubHeading>
        <p>{ai.readme_summary}</p>
        <ModelLine ai={ai} />
      </Wrapper>
    );
  }

  return (
    <Wrapper>
      <div className="flex flex-wrap items-start gap-8">
        <Stamp label="Verified" value={`${ai.confidence}/100`} color="border-moss text-moss" />
        <p className="min-w-60 flex-1 font-display text-2xl leading-snug">{ai.review.summary}</p>
      </div>
      <p className="mt-6 text-sm italic text-ink-soft">Validator said: {ai.confidence_reason}</p>

      <SubHeading>README in short</SubHeading>
      <p>{ai.readme_summary}</p>

      <SubHeading>Problems spotted</SubHeading>
      <ol className="space-y-3">
        {ai.review.problems.map((problem, index) => (
          <li key={index} className="flex gap-4">
            <span className="font-mono text-xs leading-6 text-vermilion">{String(index + 1).padStart(2, "0")}</span>
            <span>{problem}</span>
          </li>
        ))}
      </ol>

      <ModelLine ai={ai} />
    </Wrapper>
  );
}
