"use client";

import { useState } from "react";

import { downloadPdf } from "../lib/api";

export default function DownloadButton({ report }) {
  const [busy, setBusy] = useState(false);
  const [problem, setProblem] = useState("");

  async function handleClick() {
    setBusy(true);
    setProblem("");
    try {
      await downloadPdf(report);
    } catch (error) {
      setProblem(error.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex items-center gap-4">
      <button
        onClick={handleClick}
        disabled={busy}
        className="border-2 border-ink px-5 py-2.5 text-sm font-medium transition-colors hover:bg-ink hover:text-paper disabled:opacity-50"
      >
        {busy ? "Preparing..." : "Download PDF report"}
      </button>
      {problem && <span className="font-mono text-xs text-vermilion">{problem}</span>}
    </div>
  );
}
