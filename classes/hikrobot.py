import cv2
import numpy as np
import os
import sys
import importlib
import ctypes
from ctypes import byref, cast, POINTER, sizeof, c_ubyte, c_void_p
import time
from path import CONFIG_DIR
# print("checking----",CONFIG_DIR)
# =========================================================
# 1. HIKROBOT MVS IMPORT SHIM (LINUX x86_64 ROBUST)
# =========================================================
# base_mvs = os.getenv("MVCAM_COMMON_RUNENV")

# # Standard paths for MVS on Linux
# if sys.platform.startswith("linux"):
#     # Check specific 64-bit path for Linux as per SOP
#     possible_paths = [
#         CONFIG_DIR / "Python/MvImport",  # Primary target
#         CONFIG_DIR / "Python/MvImport",
#     ]
#     MVIMPORT_PATH = possible_paths[0]
#     for p in possible_paths:
#         if os.path.exists(p):
#             MVIMPORT_PATH = p
#             break
# else:
#     # Windows fallback
#     MVIMPORT_PATH = CONFIG_DIR / "Python/MvImport",

# if base_mvs and not os.path.exists(MVIMPORT_PATH):
#     MVIMPORT_PATH = CONFIG_DIR / "Python/MvImport", # os.path.join(base_mvs, "Samples", "Python", "MvImport")

MVIMPORT_PATH = CONFIG_DIR / "Python/MvImport"
# Add to path
if os.path.exists(MVIMPORT_PATH):
    if MVIMPORT_PATH not in sys.path:
        sys.path.insert(0, str(MVIMPORT_PATH))
else:
    print(f"⚠️ Warning: MVS Import path does not exist: {MVIMPORT_PATH}")

# --- Helper Utilities ---
def c_ubyte_array_to_str(arr) -> str:
    """Safely convert c_ubyte array to string."""
    try:
        raw = bytes(arr)
        raw = raw.split(b"\x00", 1)[0]
        return raw.decode("utf-8", errors="ignore").strip()
    except:
        return ""

def pick(*names):
    """Helper to safely import MVS modules dynamically."""
    for mod_name in ["MvCameraControl_class", "CameraParams_const", "MvCameraControl_header"]:
        try:
            mod = importlib.import_module(mod_name)
            for n in names:
                if hasattr(mod, n): return getattr(mod, n)
        except ImportError:
            continue
    return None

# --- Import MVS SDK ---
_HIK_OK = False
try:
    MvCamera = importlib.import_module("MvCameraControl_class").MvCamera
    
    # Constants
    MV_GIGE_DEVICE = pick("MV_GIGE_DEVICE", "MVCC_GIGE_DEVICE") or 1
    MV_USB_DEVICE = pick("MV_USB_DEVICE", "MVCC_USB_DEVICE") or 2
    MV_ACCESS_Exclusive = pick("MV_ACCESS_Exclusive", "MVCC_ACCESS_Exclusive") or 1
    
    # Structures
    MV_CC_DEVICE_INFO_LIST = pick("MV_CC_DEVICE_INFO_LIST", "MVCC_DEVICE_INFO_LIST")
    MV_CC_DEVICE_INFO = pick("MV_CC_DEVICE_INFO", "MVCC_DEVICE_INFO")
    MV_CC_PIXEL_CONVERT_PARAM = pick("MV_CC_PIXEL_CONVERT_PARAM", "MVCC_PIXEL_CONVERT_PARAM")
    MV_FRAME_OUT_INFO_EX = pick("MV_FRAME_OUT_INFO_EX", "MVCC_FRAME_OUT_INFO_EX")
    
    # Pixel Types
    PixelType_Gvsp_BGR8_Packed = pick("PixelType_Gvsp_BGR8_Packed", "PixelType_Gvsp_BGR8_Packed") or 0x02180014
    
    # Settings Structures
    FLOATVALUE = pick("MVCC_FLOATVALUE", "MV_CC_FLOATVALUE")
    ENUMVALUE = pick("MVCC_ENUMVALUE", "MV_CC_ENUMVALUE")
    ENUMENTRY = pick("MVCC_ENUMENTRY", "MV_CC_ENUMENTRY")
    INTVALUE = pick("MVCC_INTVALUE", "MV_CC_INTVALUE")

    if MvCamera and MV_CC_DEVICE_INFO:
        _HIK_OK = True
        print("✅ Hikrobot MVS SDK loaded.")
    else:
        print("⚠️ Hikrobot SDK classes missing.")
except Exception as e:
    print(f"⚠️ Hikrobot MVS SDK import failed: {e}")
    _HIK_OK = False


# =========================================================
# 2. HIKROBOT CAMERA CLASS
# =========================================================

class HikRobotCamera:
    """
    Wrapper for Hikrobot MVS Camera.
    Uses MV_CC_GetOneFrameTimeout for integration with PyQt Bridge.
    """
    def __init__(self):
        self.cam = None
        self.buf_size = 0
        self.buf_cache = None    # Raw data buffer
        self.is_running = False

    def start(self):
        if not _HIK_OK:
            print("❌ MVS SDK not loaded.")
            return False
        
        try:
            # 1. Enum Devices
            device_list = MV_CC_DEVICE_INFO_LIST()
            ctypes.memset(byref(device_list), 0, sizeof(device_list))
            ret = MvCamera.MV_CC_EnumDevices(MV_GIGE_DEVICE | MV_USB_DEVICE, device_list)
            
            if ret != 0 or device_list.nDeviceNum == 0:
                print("❌ No Hikrobot camera found.")
                return False

            # 2. Select First Device (Index 0)
            stDeviceInfo = cast(device_list.pDeviceInfo[0], POINTER(MV_CC_DEVICE_INFO)).contents
            
            # Print Model/Serial for debugging
            if stDeviceInfo.nTLayerType == MV_GIGE_DEVICE:
                info = stDeviceInfo.SpecialInfo.stGigEInfo
            else:
                info = stDeviceInfo.SpecialInfo.stUsb3VInfo
            
            model = c_ubyte_array_to_str(info.chModelName)
            serial = c_ubyte_array_to_str(info.chSerialNumber)
            print(f"🔍 Opening Camera: {model} ({serial})")

            self.cam = MvCamera()
            
            # 3. Create Handle & Open
            ret = self.cam.MV_CC_CreateHandle(stDeviceInfo)
            if ret != 0: 
                print(f"❌ CreateHandle failed: {hex(ret)}")
                return False
            
            ret = self.cam.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0)
            if ret != 0: 
                print(f"❌ OpenDevice failed: {hex(ret)}")
                self.cam.MV_CC_DestroyHandle()
                return False

            # 4. Apply Default Settings
            # Trigger Off (Continuous Mode)
            ret = self.cam.MV_CC_SetEnumValueByString("TriggerMode", "Off")
            # Auto Exposure Off
            ret = self.cam.MV_CC_SetEnumValueByString("ExposureAuto", "Off")
            # White Balance Auto OFF
            ret = self.cam.MV_CC_SetEnumValueByString("BalanceWhiteAuto", "Off")
            if ret != 0:
                print(f"⚠️ Failed to disable White Balance Auto: {hex(ret)}")

            
            # Optional: Set a default Exposure Time (e.g., 20ms = 20000us)
            self.set_exposure(123456)

            # 5. Get Payload Size (Buffer Size)
            stInt = INTVALUE()
            ctypes.memset(byref(stInt), 0, sizeof(stInt))
            ret = self.cam.MV_CC_GetIntValue("PayloadSize", stInt)
            if ret == 0 and stInt.nCurValue > 0:
                self.buf_size = int(stInt.nCurValue)
            else:
                self.buf_size = 4096 * 3072 * 3 # Safe fallback
            
            self.buf_cache = (c_ubyte * self.buf_size)()

            # 6. Start Grabbing
            ret = self.cam.MV_CC_StartGrabbing()
            if ret != 0:
                print(f"❌ Failed to start grabbing: {hex(ret)}")
                return False

            self.is_running = True
            print("✅ Hikrobot Camera Connected & Streaming")
            return True

        except Exception as e:
            print(f"❌ Hikrobot Connection Exception: {e}")
            self.close()
            return False
        
    def set_white_balance(self, r=1.0, g=1.0, b=1.0):
        try:
            self.cam.MV_CC_SetEnumValueByString("BalanceRatioSelector", "Red")
            self.cam.MV_CC_SetFloatValue("BalanceRatio", float(r))

            self.cam.MV_CC_SetEnumValueByString("BalanceRatioSelector", "Green")
            self.cam.MV_CC_SetFloatValue("BalanceRatio", float(g))

            self.cam.MV_CC_SetEnumValueByString("BalanceRatioSelector", "Blue")
            self.cam.MV_CC_SetFloatValue("BalanceRatio", float(b))
        except Exception as e:
            print(f"⚠️ Failed to set manual white balance: {e}")

    def stop(self):
        self.is_running = False
        if self.cam:
            try:
                self.cam.MV_CC_StopGrabbing()
                self.cam.MV_CC_CloseDevice()
                self.cam.MV_CC_DestroyHandle()
            except Exception as e:
                print(f"⚠️ Close Error: {e}")
        self.cam = None
        print("🔌 Hikrobot Camera Released")
        

    # def capture_raw_image(self):
    #     """
    #     Fetches one frame (timeout 1000ms), converts to BGR8, returns numpy array.
    #     Called by Bridge QTimer.
    #     """
    #     if not self.is_running or not self.cam:
    #         return None

    #     try:
    #         # Prepare Frame Info structure
    #         stFrameInfo = MV_FRAME_OUT_INFO_EX()
    #         ctypes.memset(byref(stFrameInfo), 0, sizeof(stFrameInfo))

    #         # Fetch Frame (Blocking up to 1000ms)
    #         # using buf_cache to store the raw Bayer/Mono data
    #         ret = self.cam.MV_CC_GetOneFrameTimeout(self.buf_cache, self.buf_size, stFrameInfo, 1000)
            
    #         if ret != 0:
    #             # print(f"⚠️ GetOneFrame failed: {hex(ret)}") # Uncomment for deep debugging
    #             return None

    #         # --- Pixel Conversion Logic (Same as Checking Code) ---
    #         w = stFrameInfo.nWidth
    #         h = stFrameInfo.nHeight
            
    #         # Destination buffer (BGR8 = 3 channels)
    #         dst_len = w * h * 3
    #         dst_buf = (c_ubyte * dst_len)()

    #         stConvert = MV_CC_PIXEL_CONVERT_PARAM()
    #         ctypes.memset(byref(stConvert), 0, sizeof(stConvert))
            
    #         stConvert.nWidth = w
    #         stConvert.nHeight = h
    #         stConvert.pSrcData = cast(self.buf_cache, POINTER(c_ubyte)) # Raw data
    #         stConvert.nSrcDataLen = stFrameInfo.nFrameLen
    #         stConvert.enSrcPixelType = stFrameInfo.enPixelType
    #         stConvert.enDstPixelType = PixelType_Gvsp_BGR8_Packed # Target: BGR8
    #         stConvert.pDstBuffer = cast(dst_buf, POINTER(c_ubyte)) # Target buffer
    #         stConvert.nDstBufferSize = dst_len

    #         ret = self.cam.MV_CC_ConvertPixelType(stConvert)
    #         if ret != 0:
    #             print(f"⚠️ ConvertPixelType failed: {hex(ret)}")
    #             return None

    #         # Convert c_ubyte buffer to Numpy
    #         img_arr = np.frombuffer(dst_buf, dtype=np.uint8, count=dst_len).reshape(h, w, 3)
            
    #         # Return a copy to ensure data persists after buffer reuse
    #         return img_arr.copy() 

    #     except Exception as e:
    #         print(f"❌ Capture Error: {e}")
    #         return None

    def get_frame(self):
        if not self.is_running or not self.cam:
            return None

        try:
            stFrameInfo = MV_FRAME_OUT_INFO_EX()
            ctypes.memset(byref(stFrameInfo), 0, sizeof(stFrameInfo))

            ret = self.cam.MV_CC_GetOneFrameTimeout(self.buf_cache, self.buf_size, stFrameInfo, 1000)
            if ret != 0 or stFrameInfo.nFrameLen == 0:
                return None

            w, h = stFrameInfo.nWidth, stFrameInfo.nHeight
            dst_len = w * h * 3

            # Reuse buffer
            if not hasattr(self, 'dst_buf') or len(self.dst_buf) != dst_len:
                self.dst_buf = (c_ubyte * dst_len)()

            if stFrameInfo.enPixelType != PixelType_Gvsp_BGR8_Packed:
                stConvert = MV_CC_PIXEL_CONVERT_PARAM()
                ctypes.memset(byref(stConvert), 0, sizeof(stConvert))
                stConvert.nWidth = w
                stConvert.nHeight = h
                stConvert.pSrcData = cast(self.buf_cache, POINTER(c_ubyte))
                stConvert.nSrcDataLen = stFrameInfo.nFrameLen
                stConvert.enSrcPixelType = stFrameInfo.enPixelType
                stConvert.enDstPixelType = PixelType_Gvsp_BGR8_Packed
                stConvert.pDstBuffer = cast(self.dst_buf, POINTER(c_ubyte))
                stConvert.nDstBufferSize = dst_len

                ret = self.cam.MV_CC_ConvertPixelType(stConvert)
                if ret != 0:
                    print(f"⚠️ ConvertPixelType failed: {hex(ret)}")
                    return None
                time.sleep(0.01)

                img_arr = np.frombuffer(self.dst_buf, dtype=np.uint8, count=dst_len).reshape(h, w, 3)
            else:
                img_arr = np.frombuffer(self.buf_cache, dtype=np.uint8, count=stFrameInfo.nFrameLen).reshape(h, w, 3)

            return img_arr  # No copy here; safer for streaming

        except Exception as e:
            print(f"❌ Capture Error: {e}")
            return None

    # --- Settings Helpers ---
    def get_exposure(self):
        if not self.cam or not FLOATVALUE: return 0.0
        try:
            stFloat = FLOATVALUE()
            ctypes.memset(byref(stFloat), 0, sizeof(stFloat))
            ret = self.cam.MV_CC_GetFloatValue("ExposureTime", stFloat)
            return stFloat.fCurValue if ret == 0 else 0.0
        except: return 0.0

    # def set_exposure(self, val):
    #     if not self.cam: return
    #     try:
    #         self.cam.MV_CC_SetFloatValue("ExposureTime", float(val))
    #     except Exception as e:
    #         print(f"⚠️ Failed to set exposure: {e}")

    def set_exposure(self, value):
        self.cam.MV_CC_SetFloatValue("ExposureTime", value)       


# =========================================================
# 3. WEBCAM CLASS (Fallback)
# =========================================================

class Webcam:
    def __init__(self, index=0):
        self.cap = cv2.VideoCapture(index, cv2.CAP_DSHOW) if os.name == "nt" else cv2.VideoCapture(index)
        if not self.cap or not self.cap.isOpened():
            print("❌ Webcam Initialization Failed")
            self.cap = None
        else:
            print("✅ Webcam Initialized Successfully")

    def open(self):
        return self.check_connection()

    def check_connection(self):
        return self.cap is not None and self.cap.isOpened()

    def close(self):
        if self.cap and self.cap.isOpened():
            self.cap.release()
            print("✅ Webcam closed")
        self.cap = None

    def __del__(self):
        self.close()

    def capture_raw_image(self):
        if not self.check_connection():
            return None
        ok, frame = self.cap.read()
        return frame.copy() if ok else None