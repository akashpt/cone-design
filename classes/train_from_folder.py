import cv2
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from classes.training import TrainingDetector

# folder containing BMP images
folder = Path(r"D:\final_TBD\cop_images\bmmd_60s_good")

# model name
model_key = "bmmd_60s_good"

trainer = TrainingDetector()

print("Reading images from:", folder)

# read BMP images
for img_path in folder.glob("*.bmp"):

    print("Processing:", img_path)

    img = cv2.imread(str(img_path))

    if img is None:
        print("Image read failed:", img_path)
        continue

    result = trainer.train_from_image(img, model_key)

    print("Training result:", result)