import DetectionBar from "./DetectionBar";
import Section from "./Section";
import SubHeading from "./SubHeading";

function Wrapper({ children }) {
  return (
    <Section number="04" title="AI-written code" note="A model guesses how much of the code an AI wrote. It is only an estimate." delay={225}>
      {children}
    </Section>
  );
}

function FileRow({ item }) {
  return (
    <li className="grid grid-cols-12 items-center gap-4 border-b border-rule py-2.5">
      <span className="col-span-12 break-all font-mono text-sm sm:col-span-6">{item.path}</span>
      <span className="col-span-9 h-1.5 bg-rule sm:col-span-4">
        <span className="block h-1.5 bg-ink" style={{ width: `${item.percent}%` }} />
      </span>
      <span className="col-span-3 text-right font-mono text-sm sm:col-span-2">{item.percent}%</span>
    </li>
  );
}

export default function AiDetection({ report }) {
  const detection = report.ai_detection;

  if (!detection) return null;

  if (detection.status === "skipped") {
    return (
      <Wrapper>
        <p className="text-ink-soft">There was not enough source code to make an estimate.</p>
      </Wrapper>
    );
  }

  if (detection.status === "unavailable") {
    return (
      <Wrapper>
        <p className="text-ink-soft">The AI models were not available, so no estimate was made. Scan again in a minute.</p>
      </Wrapper>
    );
  }

  return (
    <Wrapper>
      <div className="flex flex-wrap items-end gap-x-10 gap-y-4">
        <p className="font-display text-8xl font-light leading-none tabular-nums">
          {detection.percent}
          <span className="text-4xl text-ink-soft">%</span>
        </p>
        <div className="pb-2">
          <p className="font-display text-3xl italic">{detection.label}</p>
          <p className="mt-1 text-sm text-ink-soft">of the checked code looks AI-written</p>
        </div>
      </div>

      <DetectionBar percent={detection.percent} />

      <p className="font-mono text-xs text-ink-soft">
        Based on {detection.files_checked} {detection.files_checked === 1 ? "file" : "files"} &middot; {detection.lines_checked} of{" "}
        {detection.code_lines} code lines &middot; {detection.model} &middot; the model&apos;s own confidence {detection.confidence} / 100
      </p>

      <SubHeading>File by file</SubHeading>
      <ul>
        {detection.files.map((item) => (
          <FileRow key={item.path} item={item} />
        ))}
      </ul>

      {detection.signals.length > 0 && (
        <>
          <SubHeading>What the model noticed</SubHeading>
          <ul className="list-disc space-y-2 pl-5">
            {detection.signals.map((signal, index) => (
              <li key={index}>{signal}</li>
            ))}
          </ul>
        </>
      )}

      <p className="mt-10 text-sm italic text-ink-soft">
        Only an estimate by an AI model. No tool can prove who wrote code, and clean code from a careful person can look AI-written.
        Do not use it alone to judge someone.
      </p>
    </Wrapper>
  );
}
