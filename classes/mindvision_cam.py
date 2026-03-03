# classes/mindvision_cam.py

import os
import sys
import platform
import numpy as np

import os
import sys
from camera_sdk.mindvision_sdk import mvsdk


class MindVisionCamera:

    def __init__(self):
        self.hCamera = 0
        self.cap = None
        self.mono = False
        self.pFrameBuffer = None
        self.frame_buffer_size = 0

    # ==========================
    # START CAMERA
    # ==========================
    def start(self):

        if self.hCamera:
            print("MindVision already started")
            return

        devs = mvsdk.CameraEnumerateDevice()
        if not devs:
            print("No MindVision camera found")
            return

        try:
            self.hCamera = mvsdk.CameraInit(devs[0], -1, -1)
        except mvsdk.CameraException as e:
            print("CameraInit Failed:", e)
            return

        self.cap = mvsdk.CameraGetCapability(self.hCamera)

        self.mono = (self.cap.sIspCapacity.bMonoSensor != 0)

        # Set output format
        if self.mono:
            mvsdk.CameraSetIspOutFormat(
                self.hCamera,
                mvsdk.CAMERA_MEDIA_TYPE_MONO8
            )
        else:
            mvsdk.CameraSetIspOutFormat(
                self.hCamera,
                mvsdk.CAMERA_MEDIA_TYPE_BGR8
            )

        # Continuous mode
        mvsdk.CameraSetTriggerMode(self.hCamera, 0)

        # Manual exposure
        mvsdk.CameraSetAeState(self.hCamera, 0)
        mvsdk.CameraSetExposureTime(self.hCamera, 10000)

        # Start streaming
        mvsdk.CameraPlay(self.hCamera)

        # Allocate buffer
        self.frame_buffer_size = (
            self.cap.sResolutionRange.iWidthMax *
            self.cap.sResolutionRange.iHeightMax *
            (1 if self.mono else 3)
        )

        self.pFrameBuffer = mvsdk.CameraAlignMalloc(
            self.frame_buffer_size, 16
        )

        print("MindVision Camera Started")

    # ==========================
    # STOP CAMERA
    # ==========================
    def stop(self):

        if self.hCamera:
            try:
                mvsdk.CameraUnInit(self.hCamera)
            except:
                pass

            self.hCamera = 0

        if self.pFrameBuffer:
            try:
                mvsdk.CameraAlignFree(self.pFrameBuffer)
            except:
                pass

            self.pFrameBuffer = None

        print("MindVision Camera Stopped")

    # ==========================
    # GET FRAME
    # ==========================
    def get_frame(self):

        if not self.hCamera:
            return None

        try:
            pRawData, FrameHead = mvsdk.CameraGetImageBuffer(
                self.hCamera, 200
            )

            mvsdk.CameraImageProcess(
                self.hCamera,
                pRawData,
                self.pFrameBuffer,
                FrameHead
            )

            mvsdk.CameraReleaseImageBuffer(
                self.hCamera, pRawData
            )

            if platform.system() == "Windows":
                mvsdk.CameraFlipFrameBuffer(
                    self.pFrameBuffer,
                    FrameHead,
                    1
                )

            frame_data = (
                mvsdk.c_ubyte * FrameHead.uBytes
            ).from_address(self.pFrameBuffer)

            frame = np.frombuffer(frame_data, dtype=np.uint8)

            if FrameHead.uiMediaType == mvsdk.CAMERA_MEDIA_TYPE_MONO8:
                frame = frame.reshape(
                    (FrameHead.iHeight, FrameHead.iWidth)
                )
            else:
                frame = frame.reshape(
                    (FrameHead.iHeight, FrameHead.iWidth, 3)
                )

            return frame.copy()

        except mvsdk.CameraException as e:
            print("Grab error:", e)
            return None