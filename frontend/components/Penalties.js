import LedgerRow from "./LedgerRow";

export default function Penalties({ rules }) {
  if (rules.penalties.length === 0) {
    return <p className="text-ink-soft">Nothing lost. A clean 100.</p>;
  }

  return (
    <dl>
      {rules.penalties.map((item) => (
        <LedgerRow key={item.reason} label={item.reason} value={`-${item.points}`} valueClass="text-vermilion" />
      ))}
      <div className="mt-3 border-t border-ink pt-3 font-medium">
        <LedgerRow label="Rule score" value={`${rules.score} / 100`} />
      </div>
    </dl>
  );
}
