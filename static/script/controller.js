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

                if (password !== null) {
                    bridge.sendPassword(password);   // send password to python
                    setTimeout(() => bridge.goController(), 0);
                }

            };
        }

        // TRAINING
        if (training) {
            training.onclick = function () {
                if (bridge.goTraining) setTimeout(() => bridge.goTraining(), 0);
            };
        }

    });

});





window.addEventListener("load", () => {
    setTimeout(() => {
        document.getElementById("loaderDots").style.display = "none";
    }, 1400);
});