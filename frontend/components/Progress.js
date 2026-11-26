"use client";

import { useElapsed } from "../lib/useElapsed";

const SLOW_START_SECONDS = 8;

function formatTime(seconds) {
  const minutes = String(Math.floor(seconds / 60)).padStart(2, "0");
  const rest = String(seconds % 60).padStart(2, "0");
  return `${minutes}:${rest}`;
}

export default function Progress({ log }) {
  const seconds = useElapsed();
  const maybeWakingUp = log.length === 0 && seconds >= SLOW_START_SECONDS;

  return (
    <section className="reveal border-t-2 border-ink py-10">
      <div className="flex items-baseline justify-between">
        <h2 className="font-display text-3xl font-medium">
          Agents at work<span className="cursor text-vermilion">_</span>
        </h2>
        <span className="font-mono text-sm tabular-nums text-ink-soft">{formatTime(seconds)}</span>
      </div>

      <ol className="mt-8 space-y-3 font-mono text-sm">
        {log.map((step, index) => (
          <li key={index} className="reveal flex flex-col gap-1 sm:flex-row sm:gap-6">
            <span className="shrink-0 text-ink-soft sm:w-44">{step.agent}</span>
            <span>{step.message}</span>
          </li>
        ))}
        <li className="text-ink-soft">
          {maybeWakingUp ? "The free server may be waking up. This can take up to a minute." : "waiting for the next agent"}
          <span className="cursor">...</span>
        </li>
      </ol>
    </section>
  );
}
