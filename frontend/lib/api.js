const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");
const POLL_MS = 1000;

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function jsonPost(body) {
  return {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  };
}

async function callApi(path, options) {
  try {
    return await fetch(`${API_URL}${path}`, options);
  } catch {
    throw new Error("Cannot reach the server. If it was asleep, wait a minute and try again.");
  }
}

async function readJson(response) {
  let data;
  try {
    data = await response.json();
  } catch {
    throw new Error("The server is waking up. Wait a minute and try again.");
  }

  if (!response.ok) {
    throw new Error(data.detail || "Something went wrong");
  }
  return data;
}

export function pingServer() {
  fetch(`${API_URL}/health`).catch(() => {});
}

export async function runScan(url, onLog) {
  const { id } = await readJson(await callApi("/scan", jsonPost({ url })));

  while (true) {
    const scan = await readJson(await callApi(`/scan/${id}`));
    onLog(scan.log);

    if (scan.status === "done") return scan.report;
    if (scan.status === "error") throw new Error(scan.error);
    await sleep(POLL_MS);
  }
}

export async function downloadPdf(report) {
  const response = await callApi("/report/pdf", jsonPost(report));
  if (!response.ok) {
    throw new Error("Could not make the PDF");
  }

  const file = await response.blob();
  const link = document.createElement("a");
  link.href = URL.createObjectURL(file);
  link.download = "scan_report.pdf";
  link.click();
}
