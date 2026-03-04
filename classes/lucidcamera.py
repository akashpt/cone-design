from arena_api.system import system
import numpy as np
import cv2


class LucidCamera:

    def __init__(self):
        self.device = None

    def start(self):

        if self.device:
            print("Lucid already started")
            return True

        self.devices = system.create_device()

        if len(self.devices) == 0:
            print("No Lucid camera found")
            return False

        self.device = self.devices[0]
        nodemap = self.device.nodemap

        nodemap['ExposureAuto'].value = 'Off'
        nodemap['GainAuto'].value = 'Off'
        nodemap['BalanceWhiteAuto'].value = 'Off'

        nodemap['ExposureTime'].value = 115205.0
        nodemap['Gain'].value = 0.0

        self.device.start_stream()

        print("Lucid Camera Started")
        return True   # ✅ VERY IMPORTANT
    
    def stop(self):

        if self.device:
            try:
                # Just try stopping stream directly
                self.device.stop_stream()
            except Exception:
                # Ignore if already stopped
                pass

            try:
                system.destroy_device(self.devices)
            except Exception as e:
                print("Destroy error:", e)

            print("Lucid Camera Stopped")

            self.device = None
            self.devices = None

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

        # 🔵 BG conversion
        frame = cv2.cvtColor(raw, cv2.COLOR_BAYER_BG2BGR)

        self.device.requeue_buffer(buffer)

        return frame

       