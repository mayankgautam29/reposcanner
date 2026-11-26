export default function SubHeading({ children }) {
  return (
    <h3 className="mb-4 mt-10 border-b border-rule pb-2 font-mono text-xs uppercase tracking-[0.18em] text-ink-soft first:mt-0">
      {children}
    </h3>
  );
}
