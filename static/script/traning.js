document.addEventListener("DOMContentLoaded", function () {
  if (typeof qt !== "undefined") {
    new QWebChannel(qt.webChannelTransport, function (channel) {
      window.bridge = channel.objects.bridge;

      bridge.frame_signal.connect(function (imageData) {
        const img = document.getElementById("video");
        if (img) {
          img.src = "data:image/jpeg;base64," + imageData;
        }
      });
    });
  }

  // ────────────────────────────────────────────────
  //  Time & Toast
  // ────────────────────────────────────────────────
  const pad = (n) => String(n).padStart(2, "0");

  function updateTime() {
    const n = new Date();
    document.getElementById("liveTime").textContent =
      `${pad(n.getDate())}/${pad(n.getMonth() + 1)}/${n.getFullYear()} — ${pad(n.getHours())}:${pad(n.getMinutes())}:${pad(n.getSeconds())}`;
  }
  setInterval(updateTime, 1000);
  updateTime();

  function showToast(msg, icon = "fa-circle-check", color = "#4ade80") {
    const t = document.getElementById("toast");
    document.getElementById("toastMsg").textContent = msg;
    const i = t.querySelector("i");
    i.className = `fa-solid ${icon}`;
    i.style.color = color;
    t.classList.add("show");
    setTimeout(() => t.classList.remove("show"), 2800);
  }

  // ────────────────────────────────────────────────
  //  Elements
  // ────────────────────────────────────────────────
  const body = document.body;
  const statusPill = document.getElementById("statusPill");
  const statusText = document.getElementById("statusText");
  const btnStart = document.getElementById("btnStart");
  const btnStop = document.getElementById("btnStop");
  const btnLiveStart = document.getElementById("btnLiveStart");
  const btnLiveStop = document.getElementById("btnLiveStop");
  const video = document.getElementById("video");
  const placeholder = document.getElementById("placeholder");
  const camOverlay = document.getElementById("camOverlay");
  const camTag = document.getElementById("camTag");

  const startModal = document.getElementById("startModal");
  const modalMaterial = document.getElementById("modalMaterial");
  const modalCount = document.getElementById("modalCount");
  const modalYarn = document.getElementById("modalYarn");
  const modalConfirm = document.getElementById("modalConfirm");
  const modalCancel = document.getElementById("modalCancel");
  const closeModalBtn = document.getElementById("closeModal");
  const modalTrainedSelect = document.getElementById("modalTrainedSelect");
  const newModelInput = document.getElementById("newModelInput");
  const sidebarTrainedSelect = document.getElementById("trainedModelSelect");

  let stream = null;
  let uptimeSec = 0;
  let uptimeTimer = null;
  let metricsTimer = null;
  let inspected = 0;
  let defects = 0;
  let modelList = [];

  let inspectionRunning = false;
  let liveCameraRunning = false;

  // Loader
  window.addEventListener("load", () => {
    setTimeout(() => {
      document.getElementById("loaderDots").style.display = "none";
    }, 1400);
  });

  // ────────────────────────────────────────────────
  //  Button & Menu state management
  // ────────────────────────────────────────────────
  function updateButtonStates() {
    // Main inspection controls
    btnStart.disabled = inspectionRunning || liveCameraRunning;
    btnStop.disabled = !inspectionRunning;

    // Live camera controls
    btnLiveStart.disabled = liveCameraRunning || inspectionRunning;
    btnLiveStop.disabled = !liveCameraRunning;

    // Visual feedback
    btnStart.style.opacity =
      inspectionRunning || liveCameraRunning ? "0.55" : "1";
    btnLiveStart.style.opacity =
      liveCameraRunning || inspectionRunning ? "0.55" : "1";
  }

  function disableSideMenu(disable = true) {
    const aside = document.querySelector("aside");
    if (!aside) return;
    if (disable) {
      aside.classList.add("menu-disabled");
    } else {
      aside.classList.remove("menu-disabled");
    }
  }

  function updateAllStates() {
    const anyRunning = inspectionRunning || liveCameraRunning;
    disableSideMenu(anyRunning);
    updateButtonStates();
  }

  // ────────────────────────────────────────────────
  //  Modal logic
  // ────────────────────────────────────────────────
  function modalCanStart() {
    return modalMaterial.value && modalCount.value && modalYarn.value;
  }

  function updateConfirmButton() {
    modalConfirm.disabled = !modalCanStart();
  }

  [modalMaterial, modalCount, modalYarn].forEach((el) => {
    el.addEventListener("change", () => {
      el.classList.toggle("filled", !!el.value);
      updateConfirmButton();
    });
  });

  function closeStartModal() {
    startModal.style.display = "none";
  }

  startModal.onclick = (e) => {
    if (e.target === startModal) closeStartModal();
  };
  closeModalBtn.onclick = closeStartModal;
  modalCancel.onclick = closeStartModal;

  btnStart.onclick = () => {
    startModal.style.display = "flex";
    updateConfirmButton();
    syncModelsToModal();
  };

  function syncModelsToModal() {
    modalTrainedSelect.innerHTML =
      '<option value="">— Select or add new —</option>';
    modelList.forEach((m) => {
      const opt = document.createElement("option");
      opt.value = m;
      opt.textContent = m;
      modalTrainedSelect.appendChild(opt);
    });
    if (sidebarTrainedSelect.value) {
      modalTrainedSelect.value = sidebarTrainedSelect.value;
    }
  }

  // Add new model on Enter
  newModelInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      const name = newModelInput.value.trim();
      if (name && !modelList.includes(name)) {
        modelList.push(name);
        modelList.sort((a, b) => a.localeCompare(b));
        localStorage.setItem("texa_trained_models", JSON.stringify(modelList));

        syncModelsToModal();
        updateSidebarModelSelect();

        if (modelList.length > 0) {
          sidebarTrainedSelect.value = name;
        }

        newModelInput.value = "";
        showToast(`Model "${name}" added`, "fa-plus", "#16a34a");
      }
    }
  });

  function updateSidebarModelSelect() {
    const select = document.getElementById("trainedModelSelect");
    select.innerHTML = '<option value="">— Select model in modal —</option>';
    modelList.forEach((m) => {
      const opt = document.createElement("option");
      opt.value = m;
      opt.textContent = m;
      select.appendChild(opt);
    });
  }

  // ────────────────────────────────────────────────
  //  CONFIRM → Start Inspection
  // ────────────────────────────────────────────────
  modalConfirm.onclick = () => {
    if (!modalCanStart()) return;

    const selectedModel = modalTrainedSelect.value;

    // Update sidebar model display
    if (selectedModel) {
      sidebarTrainedSelect.innerHTML = `<option value="${selectedModel}" selected>${selectedModel}</option>`;
      sidebarTrainedSelect.value = selectedModel;
      sidebarTrainedSelect.classList.remove("model-display");
      void sidebarTrainedSelect.offsetWidth;
      sidebarTrainedSelect.classList.add("model-display");
    }

    // Save to backend
    if (window.bridge && bridge.saveTrainingSettings) {
      bridge.saveTrainingSettings(
        modalMaterial.value,
        modalCount.value,
        modalYarn.value,
        selectedModel,
      );
    }

    camTag.textContent = `${modalMaterial.value} · ${modalCount.value} · Yarn ${modalYarn.value}`;

    closeStartModal();
    body.classList.add("running");

    inspectionRunning = true;
    updateAllStates(); // ← buttons + side menu

    statusPill.className = "status-pill running";
    statusText.textContent = "RUNNING";

    uptimeSec = 0;
    uptimeTimer = setInterval(() => {
      uptimeSec++;
      document.getElementById("mUptime").textContent =
        `${pad(Math.floor(uptimeSec / 60))}:${pad(uptimeSec % 60)}`;
    }, 1000);

    startMetrics();

    if (window.bridge && bridge.startCamera) {
      setTimeout(() => bridge.startCamera(), 300);
    }

    video.style.display = "block";
    placeholder.style.display = "none";
  };

  function startMetrics() {
    inspected = defects = 0;
    metricsTimer = setInterval(() => {
      inspected += Math.floor(Math.random() * 4) + 1;
      if (Math.random() < 0.12) defects++;
      document.getElementById("mInspected").textContent = inspected;
      document.getElementById("mPassRate").textContent = inspected
        ? ((1 - defects / inspected) * 100).toFixed(1) + "%"
        : "—";
      document.getElementById("mDefects").textContent = defects;
      document.getElementById("signalCount").textContent = 244 + inspected;
    }, 900);
  }

  // ────────────────────────────────────────────────
  //  STOP Inspection
  // ────────────────────────────────────────────────
  btnStop.onclick = () => {
    body.classList.remove("running");

    inspectionRunning = false;
    updateAllStates(); // ← buttons + side menu

    statusPill.className = "status-pill waiting";
    statusText.textContent = "WAITING";

    clearInterval(uptimeTimer);
    clearInterval(metricsTimer);

    if (window.bridge && bridge.stopCamera) {
      bridge.stopCamera();
      placeholder.style.display = "flex";
      video.style.display = "none";
    }

    document.getElementById("mInspected").textContent = "—";
    document.getElementById("mPassRate").textContent = "—";
    document.getElementById("mDefects").textContent = "—";
    document.getElementById("mUptime").textContent = "00:00";
  };

  // ────────────────────────────────────────────────
  //  LIVE CAMERA ONLY
  // ────────────────────────────────────────────────
  btnLiveStart.onclick = () => {
    if (inspectionRunning) return;

    liveCameraRunning = true;
    updateAllStates(); // ← buttons + side menu

    statusPill.className = "status-pill running";
    statusText.textContent = "LIVE CAMERA ONLY";

    camTag.textContent = "Live view — no inspection active";

    if (window.bridge && bridge.startCamera) {
      // bridge.startCamera();
      bridge.startTrainingCapture(); // ← single frame for training (no metrics)
    }

    video.style.display = "block";
    placeholder.style.display = "none";
    camOverlay.classList.add("visible");

    showToast("Live camera started", "fa-video", "#3b82f6");
  };

  btnLiveStop.onclick = () => {
    liveCameraRunning = false;
    updateAllStates(); // ← buttons + side menu

    statusPill.className = "status-pill waiting";
    statusText.textContent = "WAITING";
    camTag.textContent = "—";

    if (window.bridge && bridge.stopCamera) {
      bridge.stopCamera();
    }

    video.style.display = "none";
    placeholder.style.display = "flex";
    camOverlay.classList.remove("visible");

    showToast("Live camera stopped", "fa-video-slash", "#ef4444");
  };

  // ────────────────────────────────────────────────
  //  Load saved models
  // ────────────────────────────────────────────────
  try {
    const saved = localStorage.getItem("texa_trained_models");
    if (saved) modelList = JSON.parse(saved);

    const lastModel = localStorage.getItem("texa_last_model");
    if (lastModel && modelList.includes(lastModel)) {
      sidebarTrainedSelect.innerHTML = `<option value="${lastModel}" selected>${lastModel}</option>`;
      sidebarTrainedSelect.value = lastModel;
    }
  } catch (e) {}

  modalConfirm.addEventListener("click", () => {
    const selected = modalTrainedSelect.value;
    if (selected) {
      localStorage.setItem("texa_last_model", selected);
    }
  });

  // ────────────────────────────────────────────────
  //  Initial state
  // ────────────────────────────────────────────────
  updateAllStates();
  btnStart.disabled = false;
});

// ────────────────────────────────────────────────
//  Aggressive zoom blocking – run last
// ────────────────────────────────────────────────
 