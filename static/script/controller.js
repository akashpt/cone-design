document.addEventListener("DOMContentLoaded", function () {

    if (typeof qt === "undefined") {
        console.log("Qt bridge not available");
        return;
    }

    new QWebChannel(qt.webChannelTransport, function (channel) {

        window.bridge = channel.objects.bridge;
        console.log("✅ Bridge connected");

        const cameraSelect = document.getElementById("cameraSelect");
        const slider = document.getElementById("expSlider");
        const input = document.getElementById("expInput");

        // camera list
        const cameras = [
            { value: "webcam", label: "Webcam" },
            { value: "hikrobot", label: "HikRobot Camera" },
            { value: "lucid", label: "Lucid Camera" },
            { value: "rtsp", label: "RTSP / IP Camera" },
            { value: "mindvision", label: "MindVision Camera" }
        ];

        // ------------------------------------------------
        // Populate dropdown
        // ------------------------------------------------
        function populateCameraSelect() {

            cameraSelect.innerHTML = '<option value="">Choose a camera…</option>';

            cameras.forEach(cam => {

                const option = document.createElement("option");
                option.value = cam.value;
                option.textContent = cam.label;

                cameraSelect.appendChild(option);

            });
        }

        populateCameraSelect();

        // ------------------------------------------------
        // Load saved settings from Python
        // ------------------------------------------------
        if (bridge.getControllerSettings) {

            bridge.getControllerSettings(function (data) {

                const settings = JSON.parse(data);

                if (settings.camera) {

                    cameraSelect.value = settings.camera;

                    if (bridge.selectCamera) {
                        bridge.selectCamera(settings.camera);
                    }

                    updateExposureRange(settings.camera);
                }

                if (settings.exposure) {

                    slider.value = settings.exposure;
                    input.value = settings.exposure;

                }

            });

        }

        // ------------------------------------------------
        // Camera change
        // ------------------------------------------------
        cameraSelect.addEventListener("change", function () {

            const cam = cameraSelect.value;

            if (!cam) return;

            console.log("Selected Camera:", cam);

            updateExposureRange(cam);

            if (bridge.selectCamera) {
                bridge.selectCamera(cam);
            }

        });

        // ------------------------------------------------
        // Save button
        // ------------------------------------------------
        const saveBtn = document.getElementById("saveSettingsBtn");

        if (saveBtn) {

            saveBtn.onclick = function () {

                const camera = cameraSelect.value;
                const exposure = slider.value;

                if (!camera) {
                    alert("Please select camera");
                    return;
                }

                if (bridge) {

                    bridge.setExposure(exposure);
                    bridge.saveControllerSettings(camera, exposure);

                }

                console.log("Saved:", camera, exposure);

            };

        }

    });

});



 function openControllerModal() {

    document.getElementById("controllerModal").style.display = "block";

}

function submitControllerPassword(){

    const password = document.getElementById("controllerPassword").value;

    if(!password) return;

    if(window.bridge){
        bridge.sendPassword(password);
    }

}

document.addEventListener("DOMContentLoaded", function(){

const saveBtn = document.getElementById("saveSettingsBtn");

if (saveBtn) {
    saveBtn.onclick = function () {

        const camera = document.getElementById("cameraValue").value;
        const exposure = document.getElementById("expSlider").value;

        if (bridge) {

            bridge.setExposure(exposure);
            bridge.saveControllerSettings(camera, exposure);

        }

        console.log("Camera:", camera);
        console.log("Exposure:", exposure);

    };
}

});


window.addEventListener("load", () => {
    setTimeout(() => {
        document.getElementById("loaderDots").style.display = "none";
    }, 1400);
});