export default function LedgerRow({ label, value, valueClass = "" }) {
  return (
    <div className="flex items-baseline gap-3 py-1.5">
      <dt>{label}</dt>
      <span className="flex-1 border-b border-dotted border-ink/40" />
      <dd className={`font-mono ${valueClass}`}>{value}</dd>
    </div>
  );
}
