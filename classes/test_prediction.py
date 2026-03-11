import cv2
from pathlib import Path
import sys

# allow import from project root
sys.path.append(str(Path(__file__).resolve().parents[1]))

from classes.prediction import PredictionDetector


# ----------------------------------
# IMAGE PATH
# ----------------------------------
image_path = r"D:\final_TBD\cop_images\bmmd_60s_good\hik_raw_20260216_145313_559.bmp"

# model key
model_key = "bmmd_60s_good"


# ----------------------------------
# LOAD IMAGE
# ----------------------------------
img = cv2.imread(image_path)

if img is None:
    print("❌ Image not found")
    exit()

print("Image loaded:", image_path)


# ----------------------------------
# RUN PREDICTION
# ----------------------------------
detector = PredictionDetector()

vis, results, bits = detector.process_frame(img, model_key)


# ----------------------------------
# PRINT RESULTS
# ----------------------------------
print("\nThread Results:", results)
print("PLC Bits:", bits)


# ----------------------------------
# SHOW IMAGE
# ----------------------------------
cv2.imshow("Prediction Result", vis)
cv2.waitKey(0)
cv2.destroyAllWindows()


# ----------------------------------
# SAVE RESULT
# ----------------------------------
save_path = "data/prediction_images/prediction_result1.jpg"
cv2.imwrite(save_path, vis)

print("Result saved:", save_path)