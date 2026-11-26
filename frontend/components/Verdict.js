"use client";

import { getZone } from "../lib/score";
import { useCountUp } from "../lib/useCountUp";
import DownloadButton from "./DownloadButton";
import Gauge from "./Gauge";
import LedgerRow from "./LedgerRow";

function getAiScoreText(ai) {
  if (ai.status === "sure") return `${ai.review.score} / 100`;
  if (ai.status === "skipped") return "skipped";
  return "not sure";
}

export default function Verdict({ report }) {
  const shownScore = useCountUp(report.final_score);
  const ai = report.ai;
  const confidence = ai.status === "skipped" ? "-" : `${ai.confidence} / 100`;

  return (
    <section className="reveal border-t-2 border-ink pt-8">
      <div className="grid gap-10 lg:grid-cols-12 lg:items-end">
        <div className="lg:col-span-7">
          <a
            href={report.url}
            target="_blank"
            rel="noreferrer"
            className="font-mono text-sm underline decoration-rule decoration-2 underline-offset-4 hover:decoration-vermilion"
          >
            {report.name}
          </a>
          <div className="mt-2 flex items-baseline gap-3">
            <span className={`font-display text-[9rem] font-light leading-none tabular-nums sm:text-[12rem] ${getZone(report.final_score).text}`}>
              {shownScore}
            </span>
            <span className="font-mono text-xl text-ink-soft">/100</span>
          </div>
          <p className="font-display text-3xl italic">{report.grade}</p>
        </div>

        <dl className="lg:col-span-5">
          <LedgerRow label="Rule score" value={`${report.rules.score} / 100`} />
          <LedgerRow label="AI score" value={getAiScoreText(ai)} />
          <LedgerRow label="AI confidence" value={confidence} />
          <div className="mt-6">
            <DownloadButton report={report} />
          </div>
        </dl>
      </div>

      <Gauge score={report.final_score} />
    </section>
  );
}
