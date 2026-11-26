export default function Secrets({ secrets }) {
  if (secrets.length === 0) {
    return (
      <p className="flex items-center gap-3">
        <span className="h-2.5 w-2.5 bg-moss" />
        No keys or passwords found in the code.
      </p>
    );
  }

  return (
    <ul className="space-y-2 font-mono text-sm">
      {secrets.map((secret, index) => (
        <li key={index} className="grid gap-1 border-l-2 border-vermilion bg-vermilion/5 px-4 py-2.5 sm:grid-cols-12 sm:gap-4">
          <span className="break-all sm:col-span-5">
            {secret.file}:{secret.line}
          </span>
          <span className="sm:col-span-4">{secret.type}</span>
          <span className="text-vermilion sm:col-span-3 sm:text-right">{secret.preview}</span>
        </li>
      ))}
    </ul>
  );
}
