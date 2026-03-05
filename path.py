from pathlib import Path


# ============================================================
# 🔥 BASE DIRECTORY (PROJECT ROOT)
# ============================================================

BASE_DIR = Path(__file__).resolve().parent


# ============================================================
# 🔥 CLASSES
# ============================================================

CLASSES_DIR = BASE_DIR / "classes"


# ============================================================
# 🔥 STATIC FILES
# ============================================================

STATIC_DIR = BASE_DIR / "static"

CSS_DIR = STATIC_DIR / "css"
JS_DIR = STATIC_DIR / "script"
IMG_DIR = STATIC_DIR / "img"
FONTS_DIR = STATIC_DIR / "fonts"
WEBFONTS_DIR = STATIC_DIR / "webfonts"


# ============================================================
# 🔥 TEMPLATES (HTML)
# ============================================================

TEMPLATES_DIR = BASE_DIR / "templates"

INDEX_PAGE = TEMPLATES_DIR / "index.html"
TRAINING_PAGE = TEMPLATES_DIR / "training.html"
CONTROLLER_PAGE = TEMPLATES_DIR / "controller.html"
REPORT_PAGE = TEMPLATES_DIR / "report.html"


# ============================================================
# 🔥 DATA / STORAGE
# ============================================================

DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

TRAINING_IMAGES_DIR = DATA_DIR / "training_images"
TRAINING_IMAGES_DIR.mkdir(exist_ok=True)

PREDICTION_IMAGES_DIR = DATA_DIR / "prediction_images"
PREDICTION_IMAGES_DIR.mkdir(exist_ok=True)


# ============================================================
# 🔥 MODELS
# ============================================================

MODELS_DIR = BASE_DIR / "models"
MODELS_DIR.mkdir(exist_ok=True)

DEFAULT_MODEL = MODELS_DIR / "best.pt"


# ============================================================
# 🔥 SETTINGS FILES
# ============================================================

SETTINGS_FILE = BASE_DIR / "settings.json"
TRAINING_SETTINGS_FILE = BASE_DIR / "training_settings.json"


# ============================================================
# 🔥 PLC SIGNAL FILES (OPTIONAL)
# ============================================================

SIGNAL_FILE = BASE_DIR / "signal.txt"
COUNT_FILE = BASE_DIR / "count.txt"


CONFIG_DIR = BASE_DIR / "camera_sdk" 