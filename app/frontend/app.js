const consoleBox = document.getElementById("consoleBox");
const healthDot = document.getElementById("healthDot");

let activeStreamController = null;

function pretty(value) {
  return JSON.stringify(value, null, 2);
}

function setConsole(value) {
  consoleBox.textContent = value;
}

function appendConsole(value) {
  consoleBox.textContent += value;
  consoleBox.scrollTop = consoleBox.scrollHeight;
}

function setText(id, value) {
  document.getElementById(id).textContent = value;
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const raw = await response.text();
  const data = raw ? JSON.parse(raw) : {};
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}\n${pretty(data)}`);
  }
  return data;
}

async function refreshOverview() {
  try {
    const [health, ragStatus, chainStatus, sources] = await Promise.all([
      api("/health/"),
      api("/rag/status"),
      api("/chains/status"),
      api("/rag/sources"),
    ]);

    setText("serviceStatus", health.status || "-");
    setText("workerStatus", health.worker_running ? "Running" : "Stopped");
    setText("queueSize", String(health.queue_size ?? "-"));
    setText("indexedChunks", String(ragStatus.indexed_chunks ?? "-"));
    setText("chainMode", chainStatus.chain_mode || "-");
    setText("chainTools", (chainStatus.tools || []).join(", ") || "-");
    setText("embeddingModel", ragStatus.embedding_model || "-");
    setText("sourcesDetected", String(sources.files_detected ?? "-"));

    if (health.status === "ok") {
      healthDot.classList.add("live");
    } else {
      healthDot.classList.remove("live");
    }
  } catch (error) {
    healthDot.classList.remove("live");
    setConsole(`Overview refresh failed:\n${error.message}`);
  }
}

function getTopK() {
  return Number(document.getElementById("ragTopK").value || 4);
}

function getChainTopK() {
  return Number(document.getElementById("chainTopK").value || 4);
}

async function runQuerySync() {
  const prompt = document.getElementById("p2Prompt").value.trim();
  if (!prompt) {
    setConsole("Enter a Phase 2 prompt.");
    return;
  }
  setConsole("Running /query/sync...");
  try {
    const data = await api("/query/sync", { method: "POST", body: JSON.stringify({ prompt }) });
    setConsole(pretty(data));
  } catch (error) {
    setConsole(`Sync query failed:\n${error.message}`);
  }
}

async function runQueryAsync() {
  const prompt = document.getElementById("p2Prompt").value.trim();
  if (!prompt) {
    setConsole("Enter a Phase 2 prompt.");
    return;
  }
  setConsole("Running /query/async...");
  try {
    const data = await api("/query/async", { method: "POST", body: JSON.stringify({ prompt }) });
    setConsole(pretty(data));
  } catch (error) {
    setConsole(`Async query failed:\n${error.message}`);
  }
}

async function compareQueryModes() {
  const prompt = document.getElementById("p2Prompt").value.trim();
  if (!prompt) {
    setConsole("Enter a Phase 2 prompt.");
    return;
  }
  setConsole("Comparing /query/sync and /query/async...");
  try {
    const sync = await api("/query/sync", { method: "POST", body: JSON.stringify({ prompt }) });
    const asyncResult = await api("/query/async", { method: "POST", body: JSON.stringify({ prompt }) });
    const syncSec = Number(sync.elapsed_seconds || 0);
    const asyncSec = Number(asyncResult.elapsed_seconds || 0);
    const report = {
      sync,
      async: asyncResult,
      comparison: {
        faster_mode: syncSec <= asyncSec ? "sync" : "async",
        delta_seconds: Math.abs(syncSec - asyncSec).toFixed(3),
      },
    };
    setConsole(pretty(report));
  } catch (error) {
    setConsole(`Compare failed:\n${error.message}`);
  }
}

async function submitJob() {
  const prompt = document.getElementById("jobPrompt").value.trim();
  if (!prompt) {
    setConsole("Enter a job prompt.");
    return;
  }
  setConsole("Submitting background job...");
  try {
    const data = await api("/jobs/submit", { method: "POST", body: JSON.stringify({ prompt }) });
    document.getElementById("jobIdInput").value = data.job_id || "";
    setConsole(pretty(data));
    refreshOverview();
  } catch (error) {
    setConsole(`Job submit failed:\n${error.message}`);
  }
}

async function pollJob() {
  const jobId = document.getElementById("jobIdInput").value.trim();
  if (!jobId) {
    setConsole("Enter or submit a job first.");
    return;
  }
  setConsole(`Polling job ${jobId}...`);
  try {
    const data = await api(`/jobs/${encodeURIComponent(jobId)}`);
    setConsole(pretty(data));
    refreshOverview();
  } catch (error) {
    setConsole(`Job poll failed:\n${error.message}`);
  }
}

async function startStream() {
  const prompt = document.getElementById("streamPrompt").value.trim();
  if (!prompt) {
    setConsole("Enter a stream prompt.");
    return;
  }
  if (activeStreamController) {
    activeStreamController.abort();
  }

  activeStreamController = new AbortController();
  setConsole("Streaming:\n");

  try {
    const res = await fetch(`/stream/stream?prompt=${encodeURIComponent(prompt)}`, {
      signal: activeStreamController.signal,
    });
    if (!res.ok || !res.body) {
      throw new Error(`Stream unavailable (${res.status})`);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const packets = buffer.split("\n\n");
      buffer = packets.pop() || "";

      for (const packet of packets) {
        const lines = packet.split("\n");
        let eventType = "message";
        let dataLine = "";
        for (const line of lines) {
          if (line.startsWith("event:")) eventType = line.slice(6).trim();
          if (line.startsWith("data:")) dataLine = line.slice(5).trim();
        }
        if (eventType === "done") {
          appendConsole("\n\n[DONE]");
          continue;
        }
        if (eventType === "metrics") {
          appendConsole(`\n\n[metrics] ${dataLine}`);
          continue;
        }
        appendConsole(dataLine);
      }
    }
  } catch (error) {
    if (error.name === "AbortError") {
      appendConsole("\n\n[stream stopped]");
    } else {
      appendConsole(`\n\nStream failed:\n${error.message}`);
    }
  } finally {
    activeStreamController = null;
  }
}

function stopStream() {
  if (activeStreamController) {
    activeStreamController.abort();
  }
}

async function ragIndex() {
  setConsole("Running RAG index...");
  try {
    const data = await api("/rag/index", { method: "POST", body: JSON.stringify({ rebuild: true }) });
    setConsole(pretty(data));
    refreshOverview();
  } catch (error) {
    setConsole(`RAG index failed:\n${error.message}`);
  }
}

async function ragSearch() {
  const query = document.getElementById("ragPrompt").value.trim();
  if (!query) {
    setConsole("Enter a RAG query.");
    return;
  }
  setConsole("Running RAG search...");
  try {
    const data = await api("/rag/search", {
      method: "POST",
      body: JSON.stringify({ query, top_k: getTopK() }),
    });
    setConsole(pretty(data));
  } catch (error) {
    setConsole(`RAG search failed:\n${error.message}`);
  }
}

async function ragAsk() {
  const prompt = document.getElementById("ragPrompt").value.trim();
  if (!prompt) {
    setConsole("Enter a RAG prompt.");
    return;
  }
  setConsole("Running RAG ask async...");
  try {
    const data = await api("/rag/ask-async", {
      method: "POST",
      body: JSON.stringify({ prompt, top_k: getTopK() }),
    });
    setConsole(pretty(data));
  } catch (error) {
    setConsole(`RAG ask failed:\n${error.message}`);
  }
}

async function runChain() {
  const prompt = document.getElementById("chainPrompt").value.trim();
  if (!prompt) {
    setConsole("Enter a chain prompt.");
    return;
  }
  setConsole("Running chain...");
  try {
    const data = await api("/chains/ask-async", {
      method: "POST",
      body: JSON.stringify({
        prompt,
        top_k: getChainTopK(),
        use_rag: document.getElementById("useRag").checked,
        use_tools: document.getElementById("useTools").checked,
      }),
    });
    setConsole(pretty(data));
  } catch (error) {
    setConsole(`Chain failed:\n${error.message}`);
  }
}

async function fetchChainLogs() {
  setConsole("Loading chain tool logs...");
  try {
    const data = await api("/chains/tools/logs?limit=50");
    setConsole(pretty(data));
  } catch (error) {
    setConsole(`Tool logs failed:\n${error.message}`);
  }
}

async function fetchRouteMetrics() {
  setConsole("Loading route latency metrics...");
  try {
    const data = await api("/demo/metrics");
    setConsole(pretty(data));
  } catch (error) {
    setConsole(`Metrics fetch failed:\n${error.message}`);
  }
}

async function runDemoSync() {
  setConsole("Running /demo/sync (about 5 seconds)...");
  try {
    const data = await api("/demo/sync");
    setConsole(pretty(data));
  } catch (error) {
    setConsole(`Demo sync failed:\n${error.message}`);
  }
}

async function runDemoAsync() {
  setConsole("Running /demo/async (about 5 seconds)...");
  try {
    const data = await api("/demo/async");
    setConsole(pretty(data));
  } catch (error) {
    setConsole(`Demo async failed:\n${error.message}`);
  }
}

document.getElementById("refreshOverviewBtn").addEventListener("click", refreshOverview);
document.getElementById("clearConsoleBtn").addEventListener("click", () => setConsole("Console cleared."));
document.getElementById("querySyncBtn").addEventListener("click", runQuerySync);
document.getElementById("queryAsyncBtn").addEventListener("click", runQueryAsync);
document.getElementById("compareQueryBtn").addEventListener("click", compareQueryModes);
document.getElementById("submitJobBtn").addEventListener("click", submitJob);
document.getElementById("pollJobBtn").addEventListener("click", pollJob);
document.getElementById("startStreamBtn").addEventListener("click", startStream);
document.getElementById("stopStreamBtn").addEventListener("click", stopStream);
document.getElementById("ragIndexBtn").addEventListener("click", ragIndex);
document.getElementById("ragSearchBtn").addEventListener("click", ragSearch);
document.getElementById("ragAskBtn").addEventListener("click", ragAsk);
document.getElementById("chainAskBtn").addEventListener("click", runChain);
document.getElementById("chainLogsBtn").addEventListener("click", fetchChainLogs);
document.getElementById("routeMetricsBtn").addEventListener("click", fetchRouteMetrics);
document.getElementById("demoSyncBtn").addEventListener("click", runDemoSync);
document.getElementById("demoAsyncBtn").addEventListener("click", runDemoAsync);

refreshOverview();
