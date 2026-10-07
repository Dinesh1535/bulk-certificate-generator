// CertiForge Dashboard JavaScript
document.addEventListener("DOMContentLoaded", () => {
  // State
  let activeJobId = null;
  let pollingInterval = null;
  let selectedCsvFile = null;

  // DOM Elements
  const tabButtons = document.querySelectorAll(".tab-btn");
  const tabContents = document.querySelectorAll(".tab-content");
  const jobForm = document.getElementById("job-form");
  const btnLoadSample = document.getElementById("btn-load-sample");
  const modeJsonBtn = document.getElementById("mode-json-btn");
  const modeCsvBtn = document.getElementById("mode-csv-btn");
  const modeJsonContainer = document.getElementById("mode-json-container");
  const modeCsvContainer = document.getElementById("mode-csv-container");
  const jsonRecipientsInput = document.getElementById("json-recipients-input");
  const csvDropzone = document.getElementById("csv-dropzone");
  const csvFileInput = document.getElementById("csv-file-input");
  const csvSelectedBadge = document.getElementById("csv-selected-badge");
  const btnDownloadSampleCsv = document.getElementById("btn-download-sample-csv");
  const btnSubmitJob = document.getElementById("btn-submit-job");
  const spinnerSubmit = document.getElementById("spinner-submit");
  const recentJobsList = document.getElementById("recent-jobs-list");

  // Monitor DOM Elements
  const noActiveJobMsg = document.getElementById("no-active-job-msg");
  const activeJobDetails = document.getElementById("active-job-details");
  const jobTitleDisplay = document.getElementById("job-title-display");
  const jobMetaDisplay = document.getElementById("job-meta-display");
  const jobStatusBadge = document.getElementById("job-status-badge");
  const btnRefreshJob = document.getElementById("btn-refresh-job");
  const btnDownloadZip = document.getElementById("btn-download-zip");
  const progressPercentLabel = document.getElementById("progress-percent-label");
  const progressCountsLabel = document.getElementById("progress-counts-label");
  const progressFillBar = document.getElementById("progress-fill-bar");
  const metricTotal = document.getElementById("metric-total");
  const metricSuccess = document.getElementById("metric-success");
  const metricFailed = document.getElementById("metric-failed");
  const metricStatus = document.getElementById("metric-status");
  const recipientsCountBadge = document.getElementById("recipients-count-badge");
  const recipientsTableBody = document.getElementById("recipients-table-body");

  // Verify DOM Elements
  const verifyForm = document.getElementById("verify-form");
  const verifyInputCode = document.getElementById("verify-input-code");
  const verifyResultCard = document.getElementById("verify-result-card");

  // Set default issue date to today
  const inputDate = document.getElementById("input-date");
  if (inputDate) {
    inputDate.value = new Date().toISOString().split("T")[0];
  }

  // Sample batch with both valid and simulated-error recipient
  const sampleRecipients = [
    {
      "recipient_name": "Dr. Sarah Connor",
      "recipient_email": "sarah.connor@example.com",
      "custom_attributes": { "grade": "Distinction", "hours": 60 }
    },
    {
      "recipient_name": "Alexander Hamilton",
      "recipient_email": "alex.hamilton@example.org",
      "custom_attributes": { "grade": "Honors", "hours": 45 }
    },
    {
      "recipient_name": "Elena Rostova",
      "recipient_email": "elena.rostova@example.com",
      "custom_attributes": { "grade": "Excellence", "hours": 50 }
    },
    {
      "recipient_name": "Marcus Aurelius",
      "recipient_email": "marcus.philosophy@example.edu",
      "custom_attributes": { "grade": "High Distinction", "hours": 80 }
    },
    {
      "recipient_name": "Corrupt Entry __FAIL_SIMULATION__",
      "recipient_email": "test.fail@example.com",
      "custom_attributes": { "note": "Demonstrates isolated failure handling" }
    }
  ];

  // Set initial sample in JSON editor
  jsonRecipientsInput.value = JSON.stringify(sampleRecipients, null, 2);

  // Tab switching
  tabButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      tabButtons.forEach(b => b.classList.remove("active"));
      tabContents.forEach(c => c.classList.remove("active"));
      btn.classList.add("active");
      const targetId = btn.getAttribute("data-tab");
      document.getElementById(targetId).classList.add("active");
    });
  });

  function switchTab(tabId) {
    const btn = document.querySelector(`[data-tab="${tabId}"]`);
    if (btn) btn.click();
  }

  // Load sample button
  btnLoadSample.addEventListener("click", () => {
    document.getElementById("input-title").value = "Certificate of Mastery";
    document.getElementById("input-event").value = "Full-Stack Python & AI Systems Architecture";
    document.getElementById("input-issuer").value = "DeepMind Developer Institute";
    document.getElementById("input-description").value = "In recognition of outstanding competence and project execution.";
    jsonRecipientsInput.value = JSON.stringify(sampleRecipients, null, 2);
    setMode("json");
  });

  // Mode switching
  function setMode(mode) {
    if (mode === "json") {
      modeJsonBtn.classList.add("active");
      modeCsvBtn.classList.remove("active");
      modeJsonContainer.classList.remove("hidden");
      modeCsvContainer.classList.add("hidden");
    } else {
      modeCsvBtn.classList.add("active");
      modeJsonBtn.classList.remove("active");
      modeCsvContainer.classList.remove("hidden");
      modeJsonContainer.classList.add("hidden");
    }
  }

  modeJsonBtn.addEventListener("click", () => setMode("json"));
  modeCsvBtn.addEventListener("click", () => setMode("csv"));

  // CSV Drag and drop
  csvDropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    csvDropzone.classList.add("dragover");
  });

  csvDropzone.addEventListener("dragleave", () => {
    csvDropzone.classList.remove("dragover");
  });

  csvDropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    csvDropzone.classList.remove("dragover");
    if (e.dataTransfer.files.length > 0) {
      handleCsvFile(e.dataTransfer.files[0]);
    }
  });

  csvFileInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) {
      handleCsvFile(e.target.files[0]);
    }
  });

  function handleCsvFile(file) {
    if (!file.name.toLowerCase().endsWith(".csv")) {
      alert("Please upload a .csv file.");
      return;
    }
    selectedCsvFile = file;
    csvSelectedBadge.textContent = `📄 Selected: ${file.name} (${Math.round(file.size / 1024)} KB)`;
    csvSelectedBadge.classList.remove("hidden");
  }

  // Sample CSV generator
  btnDownloadSampleCsv.addEventListener("click", () => {
    const csvContent = "recipient_name,recipient_email,grade,hours\n" +
      "Ada Lovelace,ada@computing.org,Distinction,40\n" +
      "Alan Turing,alan@enigma.org,High Honors,50\n" +
      "Grace Hopper,grace@navy.mil,Excellence,45\n";
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", "sample_recipients.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  });

  // Form submission
  jobForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const isCsvMode = modeCsvBtn.classList.contains("active");

    btnSubmitJob.disabled = true;
    spinnerSubmit.classList.remove("hidden");

    try {
      let response;
      if (isCsvMode) {
        if (!selectedCsvFile) {
          alert("Please select or drop a CSV file first.");
          btnSubmitJob.disabled = false;
          spinnerSubmit.classList.add("hidden");
          return;
        }

        const formData = new FormData();
        formData.append("file", selectedCsvFile);
        formData.append("title", document.getElementById("input-title").value);
        formData.append("event_name", document.getElementById("input-event").value);
        formData.append("issuer_name", document.getElementById("input-issuer").value);
        formData.append("issue_date_val", document.getElementById("input-date").value);

        response = await fetch("/api/v1/jobs/csv", {
          method: "POST",
          body: formData,
        });
      } else {
        let recipientsList;
        try {
          recipientsList = JSON.parse(jsonRecipientsInput.value);
        } catch (err) {
          alert("Invalid JSON format in Recipient List: " + err.message);
          btnSubmitJob.disabled = false;
          spinnerSubmit.classList.add("hidden");
          return;
        }

        const payload = {
          title: document.getElementById("input-title").value,
          event_name: document.getElementById("input-event").value,
          issuer_name: document.getElementById("input-issuer").value,
          issue_date: document.getElementById("input-date").value,
          description: document.getElementById("input-description").value || null,
          recipients: recipientsList,
        };

        response = await fetch("/api/v1/jobs", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
      }

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Failed to submit job");
      }

      // Success: start monitoring job
      activeJobId = data.job_id;
      switchTab("tab-monitor");
      startJobPolling(activeJobId);
      loadRecentJobs();
    } catch (err) {
      alert("Error submitting generation request: " + err.message);
    } finally {
      btnSubmitJob.disabled = false;
      spinnerSubmit.classList.add("hidden");
    }
  });

  // Polling Job Status
  function startJobPolling(jobId) {
    if (pollingInterval) clearInterval(pollingInterval);
    activeJobId = jobId;
    noActiveJobMsg.classList.add("hidden");
    activeJobDetails.classList.remove("hidden");

    fetchJobDetails(jobId);
    pollingInterval = setInterval(() => {
      fetchJobDetails(jobId);
    }, 1200);
  }

  async function fetchJobDetails(jobId) {
    try {
      const res = await fetch(`/api/v1/jobs/${jobId}`);
      if (!res.ok) return;
      const job = await res.json();
      renderJobDetails(job);

      // Stop polling when terminal state is reached
      if (["COMPLETED", "COMPLETED_WITH_ERRORS", "FAILED"].includes(job.status)) {
        clearInterval(pollingInterval);
        loadRecentJobs();
      }
    } catch (err) {
      console.error("Polling error:", err);
    }
  }

  function renderJobDetails(job) {
    jobTitleDisplay.textContent = job.title;
    jobMetaDisplay.textContent = `Event: ${job.event_name} | Issuer: ${job.issuer_name} | Date: ${job.issue_date} | Job ID: ${job.id}`;

    // Status Badge
    jobStatusBadge.className = `status-badge status-${job.status.toLowerCase()}`;
    jobStatusBadge.textContent = job.status.replace(/_/g, " ");

    // Progress Bar
    const pct = job.progress_percentage || 0;
    progressPercentLabel.textContent = `${pct}% Complete`;
    progressCountsLabel.textContent = `${job.processed_count} / ${job.total_count} Processed`;
    progressFillBar.style.width = `${pct}%`;

    // Counters
    metricTotal.textContent = job.total_count;
    metricSuccess.textContent = job.success_count;
    metricFailed.textContent = job.failed_count;
    metricStatus.textContent = job.status;

    // ZIP Button
    if (job.success_count > 0 && job.zip_download_url) {
      btnDownloadZip.href = job.zip_download_url;
      btnDownloadZip.classList.remove("disabled");
    } else {
      btnDownloadZip.classList.add("disabled");
    }

    // Recipients Table
    if (job.recipients) {
      recipientsCountBadge.textContent = `${job.recipients.length} recipients`;
      recipientsTableBody.innerHTML = job.recipients.map(r => {
        const badgeClass = `badge badge-${r.status.toLowerCase()}`;
        const downloadAction = r.download_url
          ? `<a href="${r.download_url}" target="_blank" class="btn btn-primary btn-sm">📥 Download PDF</a>`
          : `<span class="field-hint">Not generated</span>`;
        const errorText = r.error_message
          ? `<span style="color: var(--accent-danger); font-size: 11px;">${escapeHtml(r.error_message)}</span>`
          : `<span style="color: var(--text-muted);">-</span>`;

        return `
          <tr>
            <td><strong>${escapeHtml(r.recipient_name)}</strong></td>
            <td>${escapeHtml(r.recipient_email)}</td>
            <td class="code-cell">${escapeHtml(r.certificate_code)}</td>
            <td><span class="${badgeClass}">${r.status}</span></td>
            <td>${errorText}</td>
            <td>${downloadAction}</td>
          </tr>
        `;
      }).join("");
    }
  }

  btnRefreshJob.addEventListener("click", () => {
    if (activeJobId) fetchJobDetails(activeJobId);
  });

  // Recent Jobs List
  async function loadRecentJobs() {
    try {
      const res = await fetch("/api/v1/jobs?limit=6");
      if (!res.ok) return;
      const jobs = await res.json();
      if (!jobs || jobs.length === 0) {
        recentJobsList.innerHTML = `<div class="empty-state-sm">No recent jobs found.</div>`;
        return;
      }

      recentJobsList.innerHTML = jobs.map(j => {
        const statusClass = `badge badge-${j.status.toLowerCase()}`;
        return `
          <div class="recent-item" data-id="${j.id}">
            <div>
              <div style="font-weight: 600; font-size: 13px;">${escapeHtml(j.title)}</div>
              <div style="font-size: 11px; color: var(--text-muted);">${escapeHtml(j.event_name)} &bull; ${j.total_count} recipients</div>
            </div>
            <span class="${statusClass}">${j.status}</span>
          </div>
        `;
      }).join("");

      document.querySelectorAll(".recent-item").forEach(item => {
        item.addEventListener("click", () => {
          const id = item.getAttribute("data-id");
          switchTab("tab-monitor");
          startJobPolling(id);
        });
      });
    } catch (err) {
      console.error("Error loading recent jobs:", err);
    }
  }

  // Verification Form
  verifyForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const code = verifyInputCode.value.trim();
    if (!code) return;

    verifyResultCard.classList.remove("hidden");
    verifyResultCard.innerHTML = `<div style="text-align:center;">Verifying credential...</div>`;

    try {
      const res = await fetch(`/api/v1/certificates/verify/${encodeURIComponent(code)}`);
      const data = await res.json();

      if (data.is_valid) {
        verifyResultCard.className = "verify-result verify-success";
        verifyResultCard.innerHTML = `
          <div style="display:flex; align-items:center; gap:10px; margin-bottom:12px;">
            <span style="font-size:24px;">✅</span>
            <h3 style="color:var(--accent-success);">Official Certificate Verified</h3>
          </div>
          <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; font-size:13px;">
            <div><strong>Recipient:</strong> ${escapeHtml(data.recipient_name || "")}</div>
            <div><strong>Email:</strong> ${escapeHtml(data.recipient_email || "")}</div>
            <div><strong>Event / Course:</strong> ${escapeHtml(data.event_name || "")}</div>
            <div><strong>Authorized Issuer:</strong> ${escapeHtml(data.issuer_name || "")}</div>
            <div><strong>Issue Date:</strong> ${data.issue_date || "-"}</div>
            <div><strong>Credential ID:</strong> <code>${escapeHtml(data.certificate_code)}</code></div>
          </div>
        `;
      } else {
        verifyResultCard.className = "verify-result verify-invalid";
        verifyResultCard.innerHTML = `
          <div style="display:flex; align-items:center; gap:10px;">
            <span style="font-size:24px;">❌</span>
            <div>
              <h3 style="color:var(--accent-danger);">Verification Failed</h3>
              <p style="font-size:13px; color:var(--text-muted);">${escapeHtml(data.message)}</p>
            </div>
          </div>
        `;
      }
    } catch (err) {
      verifyResultCard.className = "verify-result verify-invalid";
      verifyResultCard.innerHTML = `Failed to query verification server: ${err.message}`;
    }
  });

  function escapeHtml(str) {
    if (!str) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  // Load initial jobs
  loadRecentJobs();
});
