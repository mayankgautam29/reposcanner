export default function Health({ health }) {
  return (
    <ul className="grid gap-x-8 gap-y-3 sm:grid-cols-2">
      {health.map((item) => (
        <li key={item.name} className="flex items-center gap-3">
          <span className={`h-2.5 w-2.5 ${item.found ? "bg-ink" : "border-2 border-vermilion"}`} />
          <span className="flex-1">{item.name}</span>
          <span className={`font-mono text-xs uppercase tracking-wider ${item.found ? "text-ink-soft" : "text-vermilion"}`}>
            {item.found ? "present" : "missing"}
          </span>
        </li>
      ))}
    </ul>
  );
}
