const outputBox = document.getElementById("outputBox");
const healthDot = document.getElementById("healthDot");

const nodes = {
  healthStatus: document.getElementById("healthStatus"),
  workerStatus: document.getElementById("workerStatus"),
  queueSize: document.getElementById("queueSize"),
  indexedChunks: document.getElementById("indexedChunks"),
  chainMode: document.getElementById("chainMode"),
  chainTools: document.getElementById("chainTools"),
};

let streamController = null;

function writeOutput(value) {
  outputBox.textContent = value;
}

function appendOutput(value) {
  outputBox.textContent += value;
  outputBox.scrollTop = outputBox.scrollHeight;
}

function pretty(data) {
  return JSON.stringify(data, null, 2);
}

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const text = await res.text();
  const data = text ? JSON.parse(text) : {};
  if (!res.ok) {
    throw new Error(`${res.status} ${res.statusText}\n${pretty(data)}`);
  }
  return data;
}

async function refreshHealth() {
  try {
    const data = await api("/health/");
    nodes.healthStatus.textContent = data.status || "-";
    nodes.workerStatus.textContent = data.worker_running ? "Running" : "Stopped";
    nodes.queueSize.textContent = String(data.queue_size ?? "-");
    nodes.indexedChunks.textContent = String(data?.rag?.indexed_chunks ?? "-");
    nodes.chainMode.textContent = data?.chains?.chain_mode || "-";
    nodes.chainTools.textContent = (data?.chains?.tools || []).join(", ") || "-";
    if (data.status === "ok") {
      healthDot.classList.add("live");
    } else {
      healthDot.classList.remove("live");
    }
  } catch (err) {
    healthDot.classList.remove("live");
    writeOutput(`Health refresh failed:\n${err.message}`);
  }
}

async function indexDocs() {
  writeOutput("Reindexing documents...");
  try {
    const data = await api("/rag/index", {
      method: "POST",
      body: JSON.stringify({ rebuild: true }),
    });
    writeOutput(`Index complete:\n${pretty(data)}`);
    refreshHealth();
  } catch (err) {
    writeOutput(`Index failed:\n${err.message}`);
  }
}

async function runSearch() {
  const query = document.getElementById("searchPrompt").value.trim();
  const topK = Number(document.getElementById("searchTopK").value || 4);
  if (!query) {
    writeOutput("Enter a search query first.");
    return;
  }
  writeOutput("Running retrieval search...");
  try {
    const data = await api("/rag/search", {
      method: "POST",
      body: JSON.stringify({ query, top_k: topK }),
    });
    writeOutput(pretty(data));
  } catch (err) {
    writeOutput(`Search failed:\n${err.message}`);
  }
}

async function runChain() {
  const prompt = document.getElementById("chainPrompt").value.trim();
  const topK = Number(document.getElementById("chainTopK").value || 4);
  const useRag = document.getElementById("useRag").checked;
  const useTools = document.getElementById("useTools").checked;
  if (!prompt) {
    writeOutput("Enter a chain prompt first.");
    return;
  }
  writeOutput("Running chain async...");
  try {
    const data = await api("/chains/ask-async", {
      method: "POST",
      body: JSON.stringify({
        prompt,
        top_k: topK,
        use_rag: useRag,
        use_tools: useTools,
      }),
    });
    writeOutput(pretty(data));
  } catch (err) {
    writeOutput(`Chain run failed:\n${err.message}`);
  }
}

async function runStream() {
  const prompt = document.getElementById("streamPrompt").value.trim();
  if (!prompt) {
    writeOutput("Enter a streaming prompt first.");
    return;
  }
  if (streamController) {
    streamController.abort();
  }

  streamController = new AbortController();
  writeOutput("Streaming response...\n");

  try {
    const res = await fetch(`/stream/stream?prompt=${encodeURIComponent(prompt)}`, {
      method: "GET",
      signal: streamController.signal,
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

      const chunks = buffer.split("\n\n");
      buffer = chunks.pop() || "";

      for (const chunk of chunks) {
        const lines = chunk.split("\n");
        let eventName = "message";
        let dataLine = "";
        for (const line of lines) {
          if (line.startsWith("event:")) eventName = line.slice(6).trim();
          if (line.startsWith("data:")) dataLine = line.slice(5).trim();
        }

        if (eventName === "done") {
          appendOutput("\n\n[STREAM DONE]");
          continue;
        }
        if (eventName === "metrics") {
          appendOutput(`\n\n[metrics] ${dataLine}`);
          continue;
        }
        appendOutput(dataLine);
      }
    }
  } catch (err) {
    if (err.name === "AbortError") {
      appendOutput("\n\n[stream stopped]");
    } else {
      appendOutput(`\n\nStream failed:\n${err.message}`);
    }
  } finally {
    streamController = null;
  }
}

function stopStream() {
  if (streamController) {
    streamController.abort();
  }
}

document.getElementById("refreshHealthBtn").addEventListener("click", refreshHealth);
document.getElementById("indexDocsBtn").addEventListener("click", indexDocs);
document.getElementById("searchBtn").addEventListener("click", runSearch);
document.getElementById("chainAskBtn").addEventListener("click", runChain);
document.getElementById("streamBtn").addEventListener("click", runStream);
document.getElementById("stopStreamBtn").addEventListener("click", stopStream);
document.getElementById("clearOutputBtn").addEventListener("click", () => writeOutput("Cleared."));

refreshHealth();
