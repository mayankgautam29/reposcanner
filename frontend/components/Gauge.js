"use client";

import { useEffect, useState } from "react";

import { ZONES } from "../lib/score";

export default function Gauge({ score }) {
  const [position, setPosition] = useState(0);

  useEffect(() => {
    const frame = requestAnimationFrame(() => setPosition(score));
    return () => cancelAnimationFrame(frame);
  }, [score]);

  return (
    <div className="mt-14 pb-6">
      <div className="relative h-3">
        {ZONES.map((zone) => (
          <div
            key={zone.from}
            className={`absolute inset-y-0 ${zone.bar}`}
            style={{ left: `${zone.from}%`, width: `${zone.to - zone.from}%` }}
          />
        ))}
        <div
          className="absolute -top-3 h-9 w-0.5 bg-ink transition-[left] duration-[1400ms] ease-out"
          style={{ left: `${position}%` }}
        />
        {[0, 40, 60, 80, 100].map((tick) => (
          <span
            key={tick}
            className="absolute top-5 -translate-x-1/2 font-mono text-[11px] text-ink-soft first:translate-x-0 last:-translate-x-full"
            style={{ left: `${tick}%` }}
          >
            {tick}
          </span>
        ))}
      </div>
    </div>
  );
}
