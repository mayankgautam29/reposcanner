"use client";

import { useState } from "react";

export default function UrlForm({ onScan, running }) {
  const [url, setUrl] = useState("");

  function handleSubmit(event) {
    event.preventDefault();
    onScan(url);
  }

  return (
    <form onSubmit={handleSubmit} className="mt-10 flex flex-col gap-5 sm:flex-row sm:items-end">
      <label className="block flex-1">
        <span className="font-mono text-xs uppercase tracking-[0.18em] text-ink-soft">GitHub link</span>
        <input
          type="text"
          value={url}
          onChange={(event) => setUrl(event.target.value)}
          placeholder="https://github.com/owner/repo"
          spellCheck={false}
          className="mt-2 block w-full border-0 border-b-2 border-ink bg-transparent py-3 font-mono text-base outline-none transition-colors placeholder:text-ink-soft/50 focus:border-vermilion sm:text-lg"
        />
      </label>
      <button
        type="submit"
        disabled={running || !url.trim()}
        className="group flex items-center justify-center gap-3 bg-ink px-7 py-3.5 font-medium text-paper transition-colors hover:bg-vermilion disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-ink"
      >
        {running ? "Scanning" : "Scan"}
        <span className="transition-transform group-hover:translate-x-1 group-disabled:translate-x-0">&rarr;</span>
      </button>
    </form>
  );
}
