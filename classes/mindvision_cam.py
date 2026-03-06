# classes/mindvision_cam.py

import os
import sys
import platform
import numpy as np

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

        # restart if already running
        if self.hCamera:
            print("Camera already running. Restarting...")
            self.stop()

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
        mvsdk.CameraSetExposureTime(self.hCamera, 640680)

        # Start streaming
        try:
            mvsdk.CameraPlay(self.hCamera)
        except mvsdk.CameraException as e:
            print("CameraPlay Failed:", e)
            self.stop()
            return

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

        if self.hCamera != 0:
            try:
                mvsdk.CameraUnInit(self.hCamera)
            except mvsdk.CameraException as e:
                print("CameraUnInit error:", e)

            self.hCamera = 0

        if self.pFrameBuffer is not None:
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

        if self.hCamera == 0:
            return None

        try:
            pRawData, FrameHead = mvsdk.CameraGetImageBuffer(
                self.hCamera, 1000
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

            # ignore timeout errors
            if e.error_code == -12:
                return None

            print("Grab error:", e)
            return None

    # ==========================
    # AUTO RELEASE CAMERA
    # ==========================
    def __del__(self):
        self.stop()