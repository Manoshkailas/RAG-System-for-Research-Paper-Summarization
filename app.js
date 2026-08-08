document.addEventListener("DOMContentLoaded", () => {
  // Global State
  let currentPaperId = null;
  let allPapers = [];

  // DOM Elements
  const navItems = document.querySelectorAll(".nav-item");
  const tabPages = document.querySelectorAll(".tab-page");

  const pdfUploadInput = document.getElementById("pdfUploadInput");
  const dropZone = document.getElementById("dropZone");
  const summaryLoader = document.getElementById("summaryLoader");
  const summaryContainer = document.getElementById("summaryContainer");

  const activePaperBadge = document.getElementById("activePaperBadge");
  const paperTitle = document.getElementById("paperTitle");
  const paperStats = document.getElementById("paperStats");
  const abstractText = document.getElementById("abstractText");
  const contributionsList = document.getElementById("contributionsList");
  const methodologyText = document.getElementById("methodologyText");
  const resultsText = document.getElementById("resultsText");
  const limitationsText = document.getElementById("limitationsText");

  const btnExportMD = document.getElementById("btnExportMD");
  const btnExportJSON = document.getElementById("btnExportJSON");

  const qaInput = document.getElementById("qaInput");
  const btnSendQA = document.getElementById("btnSendQA");
  const chatHistory = document.getElementById("chatHistory");

  const selectPaperA = document.getElementById("selectPaperA");
  const selectPaperB = document.getElementById("selectPaperB");
  const btnCompare = document.getElementById("btnCompare");
  const comparisonResults = document.getElementById("comparisonResults");

  const chunksContainer = document.getElementById("chunksContainer");

  // Tab Navigation
  navItems.forEach(item => {
    item.addEventListener("click", () => {
      navItems.forEach(n => n.classList.remove("active"));
      tabPages.forEach(p => p.classList.remove("active"));

      item.classList.add("active");
      const targetTab = item.getAttribute("data-tab");
      document.getElementById(targetTab).classList.add("active");
    });
  });

  // Drag & Drop Handling
  dropZone.addEventListener("click", () => pdfUploadInput.click());

  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("dragover");
  });

  dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("dragover");
  });

  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("dragover");
    if (e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  });

  pdfUploadInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) {
      handleFileUpload(e.target.files[0]);
    }
  });

  // File Upload Processing
  async function handleFileUpload(file) {
    if (!file.name.endsWith(".pdf")) {
      alert("Please upload a valid PDF file.");
      return;
    }

    summaryLoader.style.display = "block";
    summaryContainer.style.display = "none";

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("/api/upload", {
        method: "POST",
        body: formData
      });

      const data = await response.json();
      summaryLoader.style.display = "none";

      if (response.ok) {
        currentPaperId = data.paper_id;
        renderSummaryView(data);
        await loadAllPapers();
      } else {
        alert("Upload Error: " + (data.detail || "Failed to process PDF"));
      }
    } catch (err) {
      summaryLoader.style.display = "none";
      alert("Network Error: " + err.message);
    }
  }

  // Render Summary View
  function renderSummaryView(data) {
    summaryContainer.style.display = "block";

    const s = data.summary || {};
    activePaperBadge.textContent = data.title || "Paper Loaded";
    paperTitle.textContent = s.title || data.title || "Paper Summary";
    paperStats.textContent = `Pages: ${data.total_pages || 0} | Vector Chunks: ${data.total_chunks || 0}`;

    abstractText.textContent = s.abstract_summary || "Abstract not found.";

    contributionsList.innerHTML = "";
    const contribs = s.key_contributions || [];
    if (contribs.length > 0) {
      contribs.forEach(c => {
        const li = document.createElement("li");
        li.textContent = c;
        contributionsList.appendChild(li);
      });
    } else {
      contributionsList.innerHTML = "<li>No specific contributions listed.</li>";
    }

    methodologyText.textContent = s.methodology || "No methodology details.";
    resultsText.textContent = s.results || "No results details.";
    limitationsText.textContent = s.limitations || "No limitations stated.";

    // Load Chunks into Inspector
    fetchPaperChunks(data.paper_id);
  }

  // Export Buttons
  btnExportMD.addEventListener("click", () => {
    if (currentPaperId) {
      window.location.href = `/api/export/${currentPaperId}?format=markdown`;
    }
  });

  btnExportJSON.addEventListener("click", () => {
    if (currentPaperId) {
      window.location.href = `/api/export/${currentPaperId}?format=json`;
    }
  });

  // Interactive Q&A
  btnSendQA.addEventListener("click", sendUserQuery);
  qaInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") sendUserQuery();
  });

  async function sendUserQuery() {
    const question = qaInput.value.strip ? qaInput.value.strip() : qaInput.value.trim();
    if (!question) return;

    // Append User Message
    appendChatMessage("user", "You", question);
    qaInput.value = "";

    try {
      const response = await fetch("/api/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: question,
          paper_id: currentPaperId
        })
      });

      const data = await response.json();
      if (response.ok) {
        let botReply = data.answer;
        if (data.retrieved_chunks && data.retrieved_chunks.length > 0) {
          botReply += "\n\n**Retrieved Sources:**\n";
          data.retrieved_chunks.forEach(c => {
            botReply += `• [${c.section} | Page ${c.pages}] ${c.text.substring(0, 100)}...\n`;
          });
        }
        appendChatMessage("bot", "ScholarRAG Bot", botReply);
      } else {
        appendChatMessage("bot", "ScholarRAG Bot", "Error: " + data.detail);
      }
    } catch (err) {
      appendChatMessage("bot", "ScholarRAG Bot", "Network error processing request.");
    }
  }

  function appendChatMessage(role, sender, text) {
    const msgDiv = document.createElement("div");
    msgDiv.className = `chat-message ${role}`;

    const senderDiv = document.createElement("div");
    senderDiv.className = "message-sender";
    senderDiv.textContent = sender;

    const bodyDiv = document.createElement("div");
    bodyDiv.className = "message-body";
    bodyDiv.textContent = text;

    msgDiv.appendChild(senderDiv);
    msgDiv.appendChild(bodyDiv);
    chatHistory.appendChild(msgDiv);
    chatHistory.scrollTop = chatHistory.scrollHeight;
  }

  // Load All Ingested Papers for Dropdowns
  async function loadAllPapers() {
    try {
      const res = await fetch("/api/papers");
      const data = await res.json();
      allPapers = data.papers || [];

      selectPaperA.innerHTML = "";
      selectPaperB.innerHTML = "";

      allPapers.forEach(p => {
        const optA = new Option(p.title, p.paper_id);
        const optB = new Option(p.title, p.paper_id);
        selectPaperA.add(optA);
        selectPaperB.add(optB);
      });

      if (allPapers.length >= 2) {
        selectPaperB.selectedIndex = 1;
      }
    } catch (e) {
      console.error("Failed to list papers:", e);
    }
  }

  // Paper Comparison
  btnCompare.addEventListener("click", async () => {
    const idA = selectPaperA.value;
    const idB = selectPaperB.value;

    if (!idA || !idB) {
      alert("Please upload at least 2 papers to compare.");
      return;
    }

    try {
      const res = await fetch("/api/compare", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ paper_id_a: idA, paper_id_b: idB })
      });

      const data = await res.json();
      if (res.ok) {
        comparisonResults.style.display = "block";
        const c = data.comparison || {};
        document.getElementById("compProblem").textContent = c.core_problem_comparison || "-";
        document.getElementById("compMethodology").textContent = c.methodology_comparison || "-";
        document.getElementById("compResults").textContent = c.results_comparison || "-";
        document.getElementById("compRecommendation").textContent = c.recommendation || "-";
      } else {
        alert("Comparison Error: " + data.detail);
      }
    } catch (err) {
      alert("Network Error during comparison.");
    }
  });

  // Fetch Chunks for Inspector
  async function fetchPaperChunks(paperId) {
    try {
      const res = await fetch(`/api/papers/${paperId}`);
      const data = await res.json();
      if (res.ok) {
        chunksContainer.innerHTML = "";
        const chunks = data.retrieved_chunks || [];
        if (chunks.length === 0) {
          chunksContainer.innerHTML = "<p>No chunk details available.</p>";
          return;
        }

        chunks.forEach((c, idx) => {
          const div = document.createElement("div");
          div.className = "chunk-item";
          div.innerHTML = `
            <div class="chunk-header">
              <span class="chunk-tag">Chunk #${idx + 1} | ${c.section || 'General'}</span>
              <span>Pages: ${c.pages ? c.pages.join(", ") : '1'}</span>
            </div>
            <div class="chunk-snippet">${c.snippet || c.text || ''}</div>
          `;
          chunksContainer.appendChild(div);
        });
      }
    } catch (e) {
      chunksContainer.innerHTML = "<p>Error loading chunks.</p>";
    }
  }

  // Initial load
  loadAllPapers();
});
