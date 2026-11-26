function Figure({ value, label }) {
  return (
    <div>
      <p className="font-display text-4xl font-light tabular-nums">{value}</p>
      <p className="mt-1 font-mono text-xs uppercase tracking-[0.18em] text-ink-soft">{label}</p>
    </div>
  );
}

export default function Quality({ quality }) {
  return (
    <div>
      <div className="flex gap-12">
        <Figure value={quality.long_files.length} label="Long files" />
        <Figure value={quality.long_functions.length} label="Long functions" />
        <Figure value={`${quality.comment_percent}%`} label="Comments" />
      </div>

      <ul className="mt-6 space-y-1.5 font-mono text-sm text-ink-soft">
        {quality.long_files.map((item) => (
          <li key={item.file}>
            file <span className="text-ink">{item.file}</span> has {item.lines} lines
          </li>
        ))}
        {quality.long_functions.map((item, index) => (
          <li key={index}>
            function <span className="text-ink">{item.name}()</span> in {item.file} has {item.lines} lines
          </li>
        ))}
      </ul>
    </div>
  );
}
