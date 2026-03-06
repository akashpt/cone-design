document.addEventListener("DOMContentLoaded", function () {

    if (typeof qt === "undefined") {
        console.log("Qt bridge not available");
        return;
    }

    new QWebChannel(qt.webChannelTransport, function (channel) {

        window.bridge = channel.objects.bridge;
        console.log("✅ Bridge connected");

        const home = document.getElementById("menuHome");
        const report = document.getElementById("menuReport");
        const controller = document.getElementById("menuController");
        const training = document.getElementById("menuTraining");

        // HOME
        if (home) {
            home.onclick = function () {
                if (bridge.goHome) setTimeout(() => bridge.goHome(), 0);
            };
        }

        // REPORT
        if (report) {
            report.onclick = function () {
                if (bridge.goReport) setTimeout(() => bridge.goReport(), 0);
            };
        }

        // CONTROLLER (PASSWORD REQUIRED)
            if (controller) {
        controller.onclick = function () {

            let password = prompt("Enter Password");

            if (password !== null && window.bridge) {
                bridge.sendPassword(password);
            }

        };
    }

        // TRAINING
        if (training) {
            training.onclick = function () {
                if (bridge.goTraining) setTimeout(() => bridge.goTraining(), 0);
            };
        }

       
        // CAMERA SELECT
        if (cameraValue) {
            cameraValue.addEventListener("change", function () {

                const cam = cameraValue.value;

                console.log("Selected Camera:", cam);

                if (bridge.selectCamera) {
                    bridge.selectCamera(cam);
                }

            });
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
const saveBtn = document.getElementById("saveSettingsBtn");

if (saveBtn) {
    saveBtn.onclick = function () {

        const camera = document.getElementById("cameraValue").value;
        const exposure = document.getElementById("evSlider").value;

        bridge.setExposure(exposure);

        console.log("Saving Settings:");
        console.log("Camera:", camera);
        console.log("Exposure:", exposure);

        if (bridge && bridge.saveControllerSettings) {
            bridge.saveControllerSettings(camera, exposure);
        }

    };
}


window.addEventListener("load", () => {
    setTimeout(() => {
        document.getElementById("loaderDots").style.display = "none";
    }, 1400);
});