let bridge = null;

document.addEventListener("DOMContentLoaded", function(){

    if(typeof qt === "undefined"){
        console.log("Qt bridge not available");
        return;
    }

    new QWebChannel(qt.webChannelTransport, function(channel){

        bridge = channel.objects.bridge;
        console.log("✅ Bridge connected");

        const cameraSelect = document.getElementById("cameraSelect");
        const slider = document.getElementById("expSlider");
        const input = document.getElementById("expInput");
        const saveBtn = document.getElementById("saveSettingsBtn");

        const cameras = [
            { value:"webcam", label:"Webcam"},
            { value:"hikrobot", label:"HikRobot Camera"},
            { value:"lucid", label:"Lucid Camera"},
            { value:"rtsp", label:"RTSP / IP Camera"},
            { value:"mindvision", label:"MindVision Camera"}
        ];

        // Populate dropdown
        function populateCameraSelect(){

            cameraSelect.innerHTML = '<option value="">Choose a camera…</option>';

            cameras.forEach(cam=>{
                const option = document.createElement("option");
                option.value = cam.value;
                option.textContent = cam.label;
                cameraSelect.appendChild(option);
            });

        }

        populateCameraSelect();

        // Toast message
        function showToast(message){

            const toast = document.getElementById("toast");
            const msg = document.getElementById("toastMsg");

            if(!toast || !msg) return;

            msg.textContent = message;
            toast.style.display = "flex";

            setTimeout(()=>{
                toast.style.display = "none";
            },2000);

        }

        // Load saved controller settings
        if(bridge.getControllerSettings){

            bridge.getControllerSettings(function(data){

                const settings = JSON.parse(data);

                if(settings.camera){
                    cameraSelect.value = settings.camera;
                    bridge.selectCamera(settings.camera);
                }

                if(settings.exposure){
                    slider.value = settings.exposure;
                    input.value = settings.exposure;
                }

            });

        }

        // Camera change
        cameraSelect.addEventListener("change", function(){

            const cam = cameraSelect.value;

            if(!cam) return;

            bridge.selectCamera(cam);

        });

        // Slider change
        slider.addEventListener("input", function(){

            input.value = slider.value;

        });

        // Input change
        input.addEventListener("input", function(){

            slider.value = input.value;

        });

        // Save button
        saveBtn.onclick = function(){

            const camera = cameraSelect.value;
            const exposure = slider.value;

            if(!camera){
                showToast("Please select camera");
                return;
            }

            bridge.setExposure(exposure);
            bridge.saveControllerSettings(camera, exposure);

            console.log("Saved:", camera, exposure);

            showToast("Settings saved successfully");

        };

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



window.addEventListener("load", () => {
    setTimeout(() => {
        document.getElementById("loaderDots").style.display = "none";
    }, 1400);
});