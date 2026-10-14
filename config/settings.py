from pathlib import Path
import torch


# ============================================================
# PROJECT ROOT
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent


# ============================================================
# DIRECTORIES
# ============================================================

TOOLS_DIR = BASE_DIR / "tools"

EXIFTOOL_DIR = TOOLS_DIR / "exiftool"

EXIFTOOL_PATH = (
    EXIFTOOL_DIR / "exiftool.exe"
)

WEIGHTS_DIR = BASE_DIR / "weights"

DATA_DIR = BASE_DIR / "data"

INPUT_DIR = DATA_DIR / "input"

OUTPUT_DIR = DATA_DIR / "output"

SAMPLES_DIR = DATA_DIR / "samples"

REPORTS_DIR = BASE_DIR / "reports"


# ============================================================
# MODEL WEIGHTS
# ============================================================

FORGERY_MODEL_PATH = (
    WEIGHTS_DIR /
    "forgery_classifier_efficientnetb0.pth"
)

UNET_MODEL_PATH = (
    WEIGHTS_DIR /
    "unet_pro_model.pth"
)

CAMERA_MODEL_PATH = (
    WEIGHTS_DIR /
    "source_camera.pth"
)


# ============================================================
# DEVICE
# ============================================================

DEVICE = torch.device(
    "cuda"
    if torch.cuda.is_available()
    else "cpu"
)


# ============================================================
# FORGERY CLASSES
# ============================================================

FORGERY_CLASSES = [
    "ai_generated",
    "copy_move",
    "real",
    "splicing"
]


# ============================================================
# IMAGE SIZES
# ============================================================

CLASSIFIER_IMAGE_SIZE = 224

LOCALIZATION_IMAGE_SIZE = 256

CAMERA_IMAGE_SIZE = 224