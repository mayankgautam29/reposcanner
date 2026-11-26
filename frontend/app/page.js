"use client";

import { useEffect, useRef, useState } from "react";

import ErrorNote from "../components/ErrorNote";
import Hero from "../components/Hero";
import Progress from "../components/Progress";
import Report from "../components/Report";
import SiteFooter from "../components/SiteFooter";
import SiteHeader from "../components/SiteHeader";
import { pingServer, runScan } from "../lib/api";

export default function Home() {
  const [report, setReport] = useState(null);
  const [log, setLog] = useState([]);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");
  const resultsRef = useRef(null);

  useEffect(() => {
    pingServer();
  }, []);

  useEffect(() => {
    if (running || report) {
      resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, [running, report]);

  async function handleScan(url) {
    setRunning(true);
    setError("");
    setReport(null);
    setLog([]);

    try {
      setReport(await runScan(url, setLog));
    } catch (problem) {
      setError(problem.message);
    } finally {
      setRunning(false);
    }
  }

  return (
    <>
      <SiteHeader />
      <main className="mx-auto max-w-6xl px-5 sm:px-8">
        <Hero onScan={handleScan} running={running} />

        <div ref={resultsRef} className="scroll-mt-6">
          {error && <ErrorNote message={error} />}
          {running && <Progress log={log} />}
          {report && <Report report={report} />}
        </div>
      </main>
      <SiteFooter />
    </>
  );
}
