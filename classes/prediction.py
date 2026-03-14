from ultralytics import YOLO
import cv2
import sys
import numpy as np
import pandas as pd
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from path import MODELS_DIR

class PredictionDetector:

    def __init__(self):

        # ================= CONFIG =================
        self.MODEL_PATH = MODELS_DIR / r"best.pt"

        self.CENTER_PORTION_RATIO = 0.30
        self.BLOCK_PIXEL_HEIGHT = 40
        # self.FIXED_BLOCK_COUNT = 80
        # self.BLUE_MARGIN = 10.0
        self.GREEN_MARGIN = 5.0
        self.THICK_MARGIN = 6.0
        self.DENSITY_MARGIN = 0.05

        self.NUM_THREADS = 4
        self.SKIP_TOP = 2
        self.SKIP_BOTTOM = 2
        # ==========================================

        self.model = YOLO(self.MODEL_PATH)

    # ----------- SEGMENT IMAGE -------------
    def segment_image(self, img, conf_val=0.94):

        h, w = img.shape[:2]
        final_img = np.zeros_like(img)

        results = self.model(img, conf=conf_val)

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

    # ----------- EXTRACT ROIs -------------
    def extract_mask_rois(self, img):

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)

        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:self.NUM_THREADS]
        cnts = sorted(cnts, key=lambda c: cv2.boundingRect(c)[0])
        rois = []
        for c in cnts[:self.NUM_THREADS]:
            x, y, w, h = cv2.boundingRect(c)
            rois.append((x, y, x + w, y + h))

        return mask, rois

    # ----------- INSPECTION -------------
    def inspect_thickness_blue(self, img, mask, rois, ref_df):

        vis = img.copy()

        H, W = img.shape[:2]
        slot_w = W // self.NUM_THREADS
        slot_results = ["EMPTY"] * self.NUM_THREADS

        for (x0, y0, x1, y1) in rois:
            # detect which slot this ROI belongs to
            center = (x0 + x1) // 2
            thread_id = min(center // slot_w + 1, self.NUM_THREADS)

            roi_img = img[y0:y1, x0:x1]
            roi_mask = mask[y0:y1, x0:x1]

            # 🔥 ADD THIS
            if roi_mask is None or roi_mask.size == 0:
                continue

            # ===== THREAD LEVEL CENTER CALCULATION =====
            ys_full, xs_full = np.where(roi_mask > 0)
            if len(xs_full) == 0:
                continue

            thread_center_x = int(xs_full.mean())

            thread_half = int(self.CENTER_PORTION_RATIO * roi_mask.shape[1] / 2)

            thread_cx0 = max(0, thread_center_x - thread_half)
            thread_cx1 = min(roi_mask.shape[1], thread_center_x + thread_half)
           # ===========================================

            ys = np.where(roi_mask > 0)[0]
            if len(ys) == 0:
                continue

            top, bottom = ys.min(), ys.max()
            thread_height = bottom - top
            if thread_height < self.BLOCK_PIXEL_HEIGHT:
                continue

            block = thread_height / self.BLOCK_PIXEL_HEIGHT

            bad_thread = False
            # cv2.rectangle(vis, (x0, y0), (x1, y1), (0, 255, 0), 2)

            for block_id in range(self.BLOCK_PIXEL_HEIGHT):

                if block_id < self.SKIP_TOP or block_id >= self.BLOCK_PIXEL_HEIGHT- self.SKIP_BOTTOM:
                    continue

                # by1 = top + block_id * self.BLOCK_PIXEL_HEIGHT
                # by2 = min(top + (block_id + 1) * self.BLOCK_PIXEL_HEIGHT, bottom)
                by1 = int(top + block_id * block)
                by2 = int(top + (block_id + 1) * block)
                

                if by2 <= by1:
                     continue
                block_mask = roi_mask[by1:by2]
                block_img = roi_img[by1:by2]

                # ✅ SAFETY CHECK FIRST
                if block_mask is None or block_mask.size == 0:
                    continue

                # ===== APPLY THREAD CENTER TO BLOCK =====
                cm = np.zeros_like(block_mask)
                cm[:, thread_cx0:thread_cx1] = 255
                block_mask = cv2.bitwise_and(block_mask, cm)
            # ========================================

                # ys_b, xs_b = np.where(block_mask > 0)
                # if len(xs_b) == 0:
                #     continue

                # # CENTER PORTION
                # center_x = int(xs_b.mean())
                # half = int(self.CENTER_PORTION_RATIO * block_mask.shape[1] / 2)

                # cx0 = max(0, center_x - half)
                # cx1 = min(block_mask.shape[1], center_x + half)

                # cm = np.zeros_like(block_mask)
                # cm[:, cx0:cx1] = 255
                # block_mask = cv2.bitwise_and(block_mask, cm)

                pixels = block_img[block_mask > 0]
                if pixels.size == 0:
                    continue

                mean_b = float(np.mean(pixels[:, 0]))
                mean_g = float(np.mean(pixels[:, 1]))

                thickness_vals = []
                for r in range(block_mask.shape[0]):
                    cols = np.where(block_mask[r] > 0)[0]
                    if len(cols) > 0:
                        thickness_vals.append(cols[-1] - cols[0])

                if len(thickness_vals) < 2:
                    continue

                thickness = float(np.mean(thickness_vals))
                expected_area = max(1, block_mask.shape[0] * thickness)
                density = np.count_nonzero(block_mask) / expected_area

                row = ref_df[
                    (ref_df.Thread_ID == thread_id) &
                    (ref_df.Block_ID == block_id + 1)
                ]

                if len(row) == 0:
                    continue

                limits = row.iloc[0]
                # green_ok = limits.G_min - self.GREEN_MARGIN <= mean_g <= limits.G_max + self.GREEN_MARGIN
                # blue_ok = limits.B_min - self.BLUE_MARGIN <= mean_b <= limits.B_max + self.BLUE_MARGIN
                # thick_ok = limits.Th_min - self.THICK_MARGIN <= thickness <= limits.Th_max + self.THICK_MARGIN

                green_margin = self.green_margin if self.green_margin is not None else self.DEFAULT_GREEN_MARGIN

                green_ok =limits.G_min - green_margin <= mean_g <= limits.G_max + green_margin

                threshold_margin = self.threshold_margin if self.threshold_margin is not None else self.DEFAULT_THRESHOLD_MARGIN

                thick_ok = limits.Th_min - threshold_margin <= thickness <= limits.Th_max + threshold_margin

                den_ok = limits.D_min - self.DENSITY_MARGIN <= density <= limits.D_max + self.DENSITY_MARGIN

                # defect = not (blue_ok and thick_ok and den_ok)
                defect = not (green_ok and thick_ok )
                color = (0, 0, 255) if defect else (0, 255, 0)
                cv2.rectangle(vis, (x0, y0), (x1, y1), color, 2)
                # cv2.rectangle(
                #     vis,
                #     # (x0 + cx0, y0 + by1),
                #     # (x0 + cx1, y0 + by2),
                #     (x0 + thread_cx0, y0 + by1),
                #     (x0 + thread_cx1, y0 + by2),
                #     color,
                #     2
                # )
                # cv2.putText(
                # vis,
                # f"B{block_id+1} T:{thickness:.1f} D:{density:.2f} G:{mean_g:.1f}",
                # (x1+10, y0+by1+12),
                # cv2.FONT_HERSHEY_SIMPLEX,
                # 0.35,
                # color,
                # 1,
                # cv2.LINE_AA
                # )

                if defect:
                    bad_thread = True

            label = "DEFECT" if bad_thread else "GOOD"

            cv2.putText(
                vis,
                f"Thread {thread_id}: {label}",
                (x0 + 5, max(20, y0 - 30)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (0, 0, 255) if bad_thread else (0, 255, 0),
                2,
                cv2.LINE_AA
            )

            slot_results[thread_id - 1] = label

        return vis, slot_results

    # ----------- BRIDGE ENTRY -------------
    def process_frame(self, img, model_key):
        print(model_key)
        # img = cv2.imread(r"ThreadI_data\raw_images\lmmd_60s_single\train_20260207_194653_582576.bmp")
        # reference_file = MODELS_DIR / f"{model_key}_training.csv"
         # ✅ Correct file name here
        # material_folder = MODELS_DIR / model_key
        # reference_file = material_folder / f"{model_key}_training_values.csv"
        reference_file = MODELS_DIR / f"{model_key}_reference.csv"
        print("Looking for reference file at:")
        print(reference_file.resolve())
        print("Exists:", reference_file.exists())


        if not reference_file.exists():
            return img, ["MODEL_NOT_FOUND"] * self.NUM_THREADS, "0000"

        ref_df = pd.read_csv(reference_file)

        seg_img = self.segment_image(img)
        mask, rois = self.extract_mask_rois(seg_img)

        vis, results = self.inspect_thickness_blue(seg_img, mask, rois, ref_df)

        bits = "".join("1" if r == "DEFECT" else "0" for r in results)

        return vis, results, bits
 

# if __name__ == "__main__":

#     image_path = r"D:\final_TBD\cop_images\23.2.2026\bamboo_30s_defect_chk\defect_1771658797.bmp"
#     img = cv2.imread(image_path)

#     detector = PredictionDetector()

#     vis, results, bits = detector.process_frame(
#         img,
#         model_key="reference"   # must match training file name
#     )

#     print("Results:", results)
#     print("Bits:", bits)
    
#     original_name = Path(image_path).stem
#     save_name = original_name + "_inspection_blue.jpg"

#     cv2.imwrite(save_name, vis)
#     print(f"Saved {save_name}") 