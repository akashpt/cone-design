# classes/lucid_cam.py

from arena_api.system import system
import numpy as np
import cv2


class LucidCamera:

    def __init__(self):
        self.device = None

    def start(self):

        if self.device:
            print("Lucid already started")
            return

        devices = system.create_device()

        if len(devices) == 0:
            print("No Lucid camera found")
            return

        self.device = devices[0]
        nodemap = self.device.nodemap
        

        # 👇 ADD THIS LINE HERE
        # print("Current PixelFormat:", nodemap['PixelFormat'].value)

        nodemap['ExposureAuto'].value = 'Off'
        nodemap['GainAuto'].value = 'Off'
        nodemap['BalanceWhiteAuto'].value = 'Off'

        nodemap['ExposureTime'].value = 115205.0
        nodemap['Gain'].value = 0.0

        self.device.start_stream()
    # print("Lucid Camera Started")

    def stop(self):
        if self.device:
            self.device.stop_stream()
            system.destroy_device()
            self.device = None
            print("Lucid Camera Stopped")

    def get_frame(self):

        if not self.device:
            return None

        try:
            buffer = self.device.get_buffer()
        except Exception as e:
            print("Buffer error:", e)
            return None

        raw = np.ctypeslib.as_array(
            buffer.pdata,
            shape=(buffer.height, buffer.width)
        )

        pixel_format = self.device.nodemap['PixelFormat'].value
        # print("PixelFormat:", pixel_format)

        if pixel_format == "BayerRG8":
            frame = cv2.cvtColor(raw, cv2.COLOR_BAYER_BG2BGR)

        elif pixel_format == "BayerBG8":
            frame = cv2.cvtColor(raw, cv2.COLOR_BAYER_RG2BGR)

        elif pixel_format == "Mono8":
            frame = cv2.cvtColor(raw, cv2.COLOR_GRAY2BGR)

        else:
            print("Unsupported format")
            frame = raw

        self.device.requeue_buffer(buffer)

        return frame