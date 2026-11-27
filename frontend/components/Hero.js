import PipelineList from "./PipelineList";
import UrlForm from "./UrlForm";

export default function Hero({ onScan, running }) {
  return (
    <section className="grid gap-14 py-14 lg:grid-cols-12 lg:gap-12 lg:py-20">
      <div className="lg:col-span-7">
        <p className="reveal font-mono text-xs uppercase tracking-[0.18em] text-vermilion">Repository audit</p>
        <h1 className="reveal mt-5 font-display text-5xl font-medium leading-[1.03] tracking-tight sm:text-7xl" style={{ animationDelay: "80ms" }}>
          Know what is <em className="font-normal">inside</em> a repo before you trust it.
        </h1>
        <p className="reveal mt-7 max-w-xl text-lg leading-relaxed text-ink-soft" style={{ animationDelay: "160ms" }}>
          Paste a public GitHub link. Seven small agents read the code, look for leaked keys, guess how much an AI wrote and score it out of 100. A second
          model checks the first one&apos;s work.
        </p>
        <div className="reveal" style={{ animationDelay: "240ms" }}>
          <UrlForm onScan={onScan} running={running} />
        </div>
      </div>

      <aside className="lg:col-span-5 lg:pt-2">
        <PipelineList />
      </aside>
    </section>
  );
}
