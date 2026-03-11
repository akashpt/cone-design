const pad = (n) => String(n).padStart(2, "0");

function updateTime() {
  const n = new Date();
  document.getElementById("liveTime").textContent =
    `${pad(n.getDate())}/${pad(n.getMonth() + 1)}/${n.getFullYear()} — ${pad(n.getHours())}:${pad(n.getMinutes())}:${pad(n.getSeconds())}`;
}
setInterval(updateTime, 1000);
updateTime();

// ================= BRIDGE CONNECTION =================
document.addEventListener("DOMContentLoaded", function () {

      const startBtn = document.getElementById("startBtn");

      if(startBtn){
          startBtn.disabled = true;
      }

    // Safe bridge connection – works in Qt, doesn't crash in normal browser
    if (typeof qt !== 'undefined' && qt.webChannelTransport) {
        new QWebChannel(qt.webChannelTransport, function(channel) {
            window.bridge = channel.objects.bridge;

            loadSavedSettings();
            loadTrainedModels();

            bridge.frame_signal.connect(function(imageData) {
                const img = document.getElementById("video");
                if (img) {
                    img.src = "data:image/jpeg;base64," + imageData;
                }
            });
            bridge.cone_status_signal.connect(function(statuses){

            updateAllCopsStatuses(statuses);

});
            bridge.cone_status_signal.connect(function(statusArray){

             updateAllCopsStatuses(statusArray);


             bridge.setPredictionSettings(
        document.getElementById("good").value,
        document.getElementById("threshold").value
    );
    

});
        });
    } else {
        console.warn("Qt WebChannel not available – running in browser/test mode");
        window.bridge = {
            startCamera: () => console.log("[FAKE] startCamera called"),
            stopCamera:  () => console.log("[FAKE] stopCamera called"),
            saveSettings: (m, c, y) => console.log("[FAKE] saveSettings:", m, c, y),
            goReport:    () => console.log("[FAKE] goReport"),
            goTraining:  () => console.log("[FAKE] goTraining"),
            frame_signal: { connect: () => {} }
        };
    }

    const btnStart = document.getElementById("btnStart");
    const btnStop = document.getElementById("btnStop");

   
    // ───────────────────────────────────────────────────────────────
    // NEW CONTROL LOGIC: OK + RESET + LOCK AFTER CONFIRM + MENU DISABLE
    // ───────────────────────────────────────────────────────────────

    let settingsLocked    = false;
    let settingsConfirmed = false;

    const btnOk    = document.getElementById("btnOk");
    const btnReset = document.getElementById("btnReset");

    const selMaterial = document.getElementById("material");
    const selCount    = document.getElementById("count");
    const selYarn     = document.getElementById("yarn");
    const reqFields   = [selMaterial, selCount, selYarn];

    function lockDropdowns(doLock) {
        reqFields.forEach(field => {
            if (field) {
                field.disabled = doLock;
                field.style.opacity = doLock ? "0.65" : "1";
                field.style.cursor  = doLock ? "not-allowed" : "pointer";
            }
        });
    }

    function updateButtonStates() {
        const allSelected =
            (selMaterial?.value || "") !== "" &&
            (selCount?.value    || "") !== "" &&
            (selYarn?.value     || "") !== "";

        if (btnStop && !btnStop.disabled) {
            // Running → only STOP active
            if (btnStart)  btnStart.disabled  = true;
            if (btnOk)     btnOk.disabled     = true;
            if (btnReset)  btnReset.disabled  = true;
            return;
        }

        if (settingsConfirmed) {
            lockDropdowns(true);
            if (btnStart)  btnStart.disabled  = false;
            if (btnOk)     btnOk.disabled     = true;
            if (btnReset)  btnReset.disabled  = false;
        } else {
            lockDropdowns(false);
            if (btnStart)  btnStart.disabled  = true;
            if (btnOk)     btnOk.disabled     = !allSelected;
            if (btnReset)  btnReset.disabled  = true;
        }
    }

    function setMenuEnabled(enabled) {
        const menuElements = document.querySelectorAll(
            'aside .menu-item, aside a, aside .menu-item[onclick], aside .menu-section > div[onclick]'
        );
        menuElements.forEach(el => {
            if (enabled) {
                el.classList.remove('disabled');
            } else {
                el.classList.add('disabled');
            }
        });
    }

    function showToast(msg, icon = "fa-circle-check", color = "#4ade80") {
        const t = document.getElementById("toast");
        if (!t) return;
        document.getElementById("toastMsg").textContent = msg;
        const i = t.querySelector("i");
        if (i) {
            i.className = `fa-solid ${icon}`;
            i.style.color = color;
        }
        t.classList.add("show");
        setTimeout(() => t.classList.remove("show"), 2800);
    }

    const statusPill = document.getElementById("statusPill");
    const statusText = document.getElementById("statusText");
    const video = document.getElementById("video");
    const placeholder = document.getElementById("placeholder");
    const camOverlay = document.getElementById("camOverlay");
    const camTag = document.getElementById("camTag");

    let stream = null,
      uptimeSec = 0,
      uptimeTimer = null,
      metricsTimer = null;
    let inspected = 0,
      defects = 0;

    function canStart() {
      return reqFields.every((el) => el.value !== "") && btnStop.disabled;
    }

    function startMetrics() {
      inspected = 0;
      defects = 0;
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

    function safeSet(id, value) {
      const el = document.getElementById(id);
      if (el) el.textContent = value;
    }

    // Dropdown change handler – updated to use new state logic
    reqFields.forEach((el) => {
      if (el) {
        el.addEventListener("change", () => {
          el.classList.toggle("filled", el.value !== "");
          updateButtonStates();
        });
      }
    });

    // OK button – confirm settings
    if (btnOk) {
      btnOk.addEventListener("click", () => {
        settingsConfirmed = true;
        updateButtonStates();

        if (window.bridge) {
          bridge.saveSettings(
            selMaterial?.value || "",
            selCount?.value    || "",
            selYarn?.value     || ""
          );
        }

        showToast("Settings confirmed — ready to start", "fa-check", "#22c55e");
      });
    }

    // RESET button
    if (btnReset) {
      btnReset.addEventListener("click", () => {
        settingsConfirmed = false;
        settingsLocked = false;
        updateButtonStates();

        showToast("Settings reset — choose again", "fa-rotate-left", "#f59e0b");
      });
    }

    // START button – updated
    btnStart.onclick = () => {
      if (!bridge || !settingsConfirmed) return;

      btnStart.disabled = true;
      btnStop.disabled  = false;

      // Disable sidebar menu
      setMenuEnabled(false);

      statusPill.className = "status-pill running";
      statusText.textContent = "RUNNING";

      camTag.textContent = `${selMaterial?.value || "—"} · ${selCount?.value || "—"} · Yarn ${selYarn?.value || "—"}`;

      uptimeSec = 0;
      uptimeTimer = setInterval(() => {
        uptimeSec++;
        document.getElementById("mUptime").textContent =
          `${pad(Math.floor(uptimeSec / 60))}:${pad(uptimeSec % 60)}`;
      }, 1000);

      startMetrics();
      bridge.startCamera();

      updateButtonStates();
    };

    // STOP button – updated
    btnStop.onclick = () => {
      if (!bridge) return;

      btnStop.disabled = true;

      // Re-enable sidebar menu
      setMenuEnabled(true);

      statusPill.className = "status-pill waiting";
      statusText.textContent = "WAITING";

      clearInterval(uptimeTimer);
      clearInterval(metricsTimer);

      bridge.stopCamera();

      document.getElementById("mInspected").textContent = "—";
      document.getElementById("mPassRate").textContent = "—";
      document.getElementById("mDefects").textContent = "—";
      document.getElementById("mUptime").textContent = "00:00";

      updateButtonStates();
    };

    // Load saved config
    try {
      const s = JSON.parse(localStorage.getItem("texa_cfg") || "{}");
      if (s.material) {
        selMaterial.value = s.material;
        selMaterial.classList.add("filled");
      }
      if (s.count) {
        selCount.value = s.count;
        selCount.classList.add("filled");
      }
      if (s.yarn) {
        selYarn.value = s.yarn;
        selYarn.classList.add("filled");
      }
      if (s.good) document.getElementById("good").value = s.good;
      if (s.threshold) document.getElementById("threshold").value = s.threshold;
    } catch (e) {}

    updateButtonStates();

function loadSavedSettings(){

    if(!bridge) return;

    bridge.getSavedSettings(function(data){

        const settings = JSON.parse(data);

        if(settings.material){
            selMaterial.value = settings.material;
            selMaterial.classList.add("filled");
        }

        if(settings.count){
            selCount.value = settings.count;
            selCount.classList.add("filled");
        }

        if(settings.yarn){
            selYarn.value = settings.yarn;
            selYarn.classList.add("filled");
        }

        // AUTO CONFIRM SETTINGS
        if(settings.material && settings.count && settings.yarn){
            settingsConfirmed = true;
        }

        updateButtonStates();

    });

}


function loadTrainedModels(){

    if(!bridge) return;

    bridge.getTrainedModels(function(data){

        const models = JSON.parse(data);

        const materialSet = new Set();
        const countSet = new Set();
        const yarnSet = new Set();

        models.forEach(model => {

            const parts = model.split("_");

            if(parts.length === 3){
                materialSet.add(parts[0]);
                countSet.add(parts[1]);
                yarnSet.add(parts[2]);
            }

        });

        const materialSelect = document.getElementById("material");
        const countSelect = document.getElementById("count");
        const yarnSelect = document.getElementById("yarn");

        materialSet.forEach(v=>{
            const opt=document.createElement("option");
            opt.text=v;
            materialSelect.add(opt);
        });

        countSet.forEach(v=>{
            const opt=document.createElement("option");
            opt.text=v;
            countSelect.add(opt);
        });

        yarnSet.forEach(v=>{
            const opt=document.createElement("option");
            opt.text=v;
            yarnSelect.add(opt);
        });

    });

}



    window.addEventListener("load", () => {
      setTimeout(
        () => (document.getElementById("loaderDots").style.display = "none"),
        1400,
      );
    });
});