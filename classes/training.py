from ultralytics import YOLO
import cv2
import numpy as np
import pandas as pd
import os
from path import MODELS_DIR


class TrainingDetector:

    def __init__(self):

        # ================= CONFIG =================
        self.MODEL_PATH = MODELS_DIR / r"best.pt"

        self.CENTER_PORTION_RATIO = 0.30
        self.BLOCK_PIXEL_HEIGHT = 40
        self.SKIP_TOP = 2
        self.SKIP_BOTTOM = 2
        self.NUM_THREADS = 4
        # ==========================================

        self.model = YOLO(self.MODEL_PATH)

    # ----------- SEGMENT IMAGE -------------
    def segment_image(self, img):

        h, w = img.shape[:2]
        final_img = np.zeros_like(img)

        results = self.model(img, conf=0.30)

        for r in results:
            if r.masks is None:
                continue

            masks = r.masks.data.cpu().numpy()

            for mask in masks:
                mask = (mask * 255).astype(np.uint8)
                mask = cv2.resize(mask, (w, h), interpolation=cv2.INTER_NEAREST)

                masked = cv2.bitwise_and(img, img, mask=mask)
                final_img = cv2.bitwise_or(final_img, masked)

        return final_img

    # ----------- PROCESS IMAGE -------------
    def process_image(self, img):

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)

        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:self.NUM_THREADS]
        cnts = sorted(cnts, key=lambda c: cv2.boundingRect(c)[0])

        results = []
        vis = img.copy()
        thread_id = 1

        for c in cnts:

            x, y, wc, hc = cv2.boundingRect(c)

            roi_img = img[y:y+hc, x:x+wc]
            roi_mask = mask[y:y+hc, x:x+wc]
            
            # ===== THREAD LEVEL CENTER CALCULATION =====
            ys_full, xs_full = np.where(roi_mask > 0)
            if len(xs_full) == 0:
                continue

            thread_center_x = int(xs_full.mean())

            thread_half = int(self.CENTER_PORTION_RATIO * roi_mask.shape[1] / 2)

            thread_cx0 = max(0, thread_center_x - thread_half)
            thread_cx1 = min(roi_mask.shape[1], thread_center_x + thread_half)



            ys = np.where(roi_mask > 0)[0]
            if len(ys) == 0:
                continue

            top, bottom = ys.min(), ys.max()
            thread_height = bottom - top
            blocks = thread_height // self.BLOCK_PIXEL_HEIGHT

            for block_id in range(blocks):

                if block_id < self.SKIP_TOP or block_id >= blocks - self.SKIP_BOTTOM:
                    continue

                by1 = top + block_id * self.BLOCK_PIXEL_HEIGHT
                by2 = min(top + (block_id + 1) * self.BLOCK_PIXEL_HEIGHT, bottom)

                block_mask = roi_mask[by1:by2]
                block_img = roi_img[by1:by2]

                # # ===== CENTER PORTION =====
                # ys_b, xs_b = np.where(block_mask > 0)
                # if len(xs_b) == 0:
                #     continue

                # center_x = int(xs_b.mean())
                # half = int(self.CENTER_PORTION_RATIO * block_mask.shape[1] / 2)

                # cx0 = max(0, center_x - half)
                # cx1 = min(block_mask.shape[1], center_x + half)

                # cm = np.zeros_like(block_mask)
                # cm[:, cx0:cx1] = 255
                # block_mask = cv2.bitwise_and(block_mask, cm)
                # ===========================

                 # ===== APPLY THREAD CENTER TO BLOCK =====
                cm = np.zeros_like(block_mask)
                cm[:, thread_cx0:thread_cx1] = 255
                block_mask = cv2.bitwise_and(block_mask, cm)
                # # ========================================

                pixels = block_img[block_mask > 0]
                if pixels.size == 0:
                    continue

                mean_b, mean_g, mean_r = np.mean(pixels, axis=0)

                thickness_vals = []
                for r in range(block_mask.shape[0]):
                    cols = np.where(block_mask[r] > 0)[0]
                    if len(cols) > 0:
                        thickness_vals.append(cols[-1] - cols[0])

                if len(thickness_vals) < 5:
                    continue

                thickness = float(np.mean(thickness_vals))
                density = np.count_nonzero(block_mask) / (block_mask.shape[0] * thickness)

                results.append([
                    thread_id,
                    block_id + 1,
                    thickness,
                    density,
                    mean_r,
                    mean_g,
                    mean_b
                ])
                    # cv2.line(vis,(x,y+by1),(x+wc,y+by1),(255,0,0),1)
                cv2.rectangle(
                        vis,
                        # (x + cx0, y + by1),
                        # (x + cx1, y + by2),
                        (x + thread_cx0, y + by1),
                        (x + thread_cx1, y + by2),

                        (0, 120, 0),
                        1
                    )

                cv2.putText(vis,
                                f"B{block_id+1} T:{thickness:.1f} D:{density:.2f} "
                                f"R:{int(mean_r)} G:{int(mean_g)} B:{int(mean_b)}",
                                (x+wc+10,y+by1+12),
                                cv2.FONT_HERSHEY_SIMPLEX,0.35,(0,255,255),1)

                thread_id+=1

        
            thread_id += 1
        return results

    # ----------- BRIDGE ENTRY POINT -------------
    # def train_from_image(self, img):

    #     seg_img = self.segment_image(img)
    #     results = self.process_image(seg_img)

    #     if len(results) == 0:
    #         return {"ok": False, "message": "No threads detected"}

    #     df = pd.DataFrame(results, columns=[
    #         "Thread_ID", "Block_ID",
    #         "Thickness", "Density",
    #         "R", "G", "B"
    #     ])

    #     reference = df.groupby(["Thread_ID", "Block_ID"]).agg({
    #         "Thickness": ["min", "max"],
    #         "Density": ["min", "max"],
    #         "R": ["min", "max"],
    #         "G": ["min", "max"],
    #         "B": ["min", "max"]
    #     }).reset_index()

    #     reference.columns = [
    #         "Thread_ID", "Block_ID",
    #         "Th_min", "Th_max",
    #         "D_min", "D_max",
    #         "R_min", "R_max",
    #         "G_min", "G_max",
    #         "B_min", "B_max"
    #     ]

    #     reference.to_csv("latest_reference.csv", index=False)

    #     return {"ok": True}

    def train_from_image(self, img,model_key):
        # print(model_key)
        # img = cv2.imread(r"ThreadI_data\raw_images\lmmd_60s_single\train_20260207_194653_582576.bmp")
        seg_img = self.segment_image(img)
        results = self.process_image(seg_img)

        if len(results) == 0:
            return {"ok": False, "message": "No threads detected"}

        # ---------- NEW DATA ----------
        new_df = pd.DataFrame(results, columns=[
            "Thread_ID", "Block_ID",
            "Thickness", "Density",
            "R", "G", "B"
        ])

        raw_data_file = MODELS_DIR/f"{model_key}_training.csv"

        # ---------- APPEND LOGIC ----------
        if os.path.exists(raw_data_file):
            old_df = pd.read_csv(raw_data_file)
            combined_df = pd.concat([old_df, new_df], ignore_index=True)
        else:
            combined_df = new_df

        # Save cumulative raw data
        combined_df.to_csv(raw_data_file, index=False)

        # ---------- GENERATE UPDATED REFERENCE ----------
        reference = combined_df.groupby(["Thread_ID", "Block_ID"]).agg({
            "Thickness": ["min", "max"],
            "Density": ["min", "max"],
            "R": ["min", "max"],
            "G": ["min", "max"],
            "B": ["min", "max"]
        }).reset_index()

        reference.columns = [
            "Thread_ID", "Block_ID",
            "Th_min", "Th_max",
            "D_min", "D_max",
            "R_min", "R_max",
            "G_min", "G_max",
            "B_min", "B_max"
        ]

        # Save updated reference
        # reference.to_csv(raw_data_file, index=False)
        reference_file = MODELS_DIR / f"{model_key}_reference.csv"
        reference.to_csv(reference_file, index=False)

        return {"ok": True}

# img = cv2.imread(r"/home/texa_innovates/Dharanidhara_Project/ThreadI_data/models/defects/defect_1770978483.bmp")
# train = TrainingDetector()
# data = train.train_from_image(img,"lmmd_60s_single")
# print(data)