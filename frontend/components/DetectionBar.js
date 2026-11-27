"use client";

import { useEffect, useState } from "react";

const ZONES = [
  { from: 0, to: 30, name: "human", tint: "bg-ink/10" },
  { from: 30, to: 70, name: "mixed", tint: "bg-ink/20" },
  { from: 70, to: 100, name: "AI", tint: "bg-ink/30" },
];

export default function DetectionBar({ percent }) {
  const [position, setPosition] = useState(0);

  useEffect(() => {
    const frame = requestAnimationFrame(() => setPosition(percent));
    return () => cancelAnimationFrame(frame);
  }, [percent]);

  return (
    <div className="mt-8 pb-10">
      <div className="relative h-3">
        {ZONES.map((zone) => (
          <div
            key={zone.name}
            className={`absolute inset-y-0 ${zone.tint}`}
            style={{ left: `${zone.from}%`, width: `${zone.to - zone.from}%` }}
          />
        ))}
        <div
          className="absolute -top-3 h-9 w-0.5 bg-ink transition-[left] duration-[1400ms] ease-out"
          style={{ left: `${position}%` }}
        />
        {ZONES.map((zone) => (
          <span
            key={zone.name}
            className="absolute top-5 -translate-x-1/2 font-mono text-[11px] text-ink-soft"
            style={{ left: `${(zone.from + zone.to) / 2}%` }}
          >
            {zone.name}
          </span>
        ))}
      </div>
    </div>
  );
}
