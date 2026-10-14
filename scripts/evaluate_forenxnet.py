from pathlib import Path
import sys
import csv
import json
import time
import traceback

import numpy as np
import torch
from PIL import Image

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_score,
    recall_score,
    f1_score,
    jaccard_score,
)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

EVALUATION_DIR = PROJECT_ROOT / "data" / "evaluation"
MASK_DIR = PROJECT_ROOT / "data" / "evaluation_masks"
OUTPUT_DIR = PROJECT_ROOT / "reports" / "evaluation"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CLASS_NAMES = [
    "ai_generated",
    "copy_move",
    "real",
    "splicing",
]

IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"
}


# ============================================================
# IMPORT EXISTING PIPELINE
# ============================================================

sys.path.insert(0, str(PROJECT_ROOT))

from services.forenxnet_pipeline import ForenXNetPipeline


# ============================================================
# UTILITIES
# ============================================================

def to_numpy_mask(value):
    """Convert a tensor/array mask to a 2D NumPy array."""

    if isinstance(value, torch.Tensor):
        value = value.detach().cpu().numpy()

    value = np.asarray(value)

    # Remove batch/channel dimensions where present.
    value = np.squeeze(value)

    if value.ndim != 2:
        raise ValueError(
            f"Expected a 2D mask after squeezing, got {value.shape}"
        )

    return value


def load_ground_truth_mask(mask_path, target_shape):
    """
    Load a binary mask.

    Black = untouched pixels
    White = manipulated pixels

    Nearest-neighbor resizing preserves binary mask values.
    """

    with Image.open(mask_path) as image:
        image = image.convert("L")
        image = image.resize(
            (target_shape[1], target_shape[0]),
            Image.Resampling.NEAREST,
        )
        mask = np.asarray(image)

    return mask >= 128


def calculate_localization_metrics(prediction, ground_truth):
    """Calculate binary localization metrics."""

    prediction = prediction.astype(bool)
    ground_truth = ground_truth.astype(bool)

    tp = int(np.logical_and(prediction, ground_truth).sum())
    fp = int(np.logical_and(prediction, ~ground_truth).sum())
    fn = int(np.logical_and(~prediction, ground_truth).sum())
    tn = int(np.logical_and(~prediction, ~ground_truth).sum())

    union = tp + fp + fn
    predicted_positive = tp + fp
    actual_positive = tp + fn

    iou = tp / union if union else 1.0

    dice_denominator = 2 * tp + fp + fn
    dice = (
        (2 * tp) / dice_denominator
        if dice_denominator
        else 1.0
    )

    precision = (
        tp / predicted_positive
        if predicted_positive
        else 0.0
    )

    recall = (
        tp / actual_positive
        if actual_positive
        else 0.0
    )

    return {
        "iou": iou,
        "dice": dice,
        "precision": precision,
        "recall": recall,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
    }


def find_images():
    """Collect images from the four class directories."""

    samples = []

    for class_name in CLASS_NAMES:
        class_dir = EVALUATION_DIR / class_name

        if not class_dir.exists():
            print(f"[WARNING] Missing directory: {class_dir}")
            continue

        for image_path in sorted(class_dir.iterdir()):
            if (
                image_path.is_file()
                and image_path.suffix.lower() in IMAGE_EXTENSIONS
            ):
                samples.append((image_path, class_name))

    return samples


# ============================================================
# MAIN EVALUATION
# ============================================================

def main():

    print("=" * 65)
    print("FORENXNET BASELINE EVALUATION")
    print("=" * 65)

    samples = find_images()

    if not samples:
        raise RuntimeError(
            f"No evaluation images found in:\n{EVALUATION_DIR}"
        )

    print(f"Evaluation images: {len(samples)}")
    print(f"Output directory: {OUTPUT_DIR}")

    # Load the existing models once.
    pipeline = ForenXNetPipeline()

    y_true = []
    y_pred = []

    classification_rows = []
    localization_rows = []
    failed_rows = []

    start_time = time.perf_counter()

    # --------------------------------------------------------
    # PROCESS EVERY IMAGE
    # --------------------------------------------------------

    for index, (image_path, true_class) in enumerate(samples, 1):

        print(
            f"\n[{index}/{len(samples)}] "
            f"{true_class}/{image_path.name}"
        )

        try:
            result = pipeline.analyze(image_path)

            classification = result["forgery_classification"]
            localization = result["localization"]

            predicted_class = classification["predicted_class"]
            confidence = float(classification["confidence"])

            probabilities = classification.get(
                "class_probabilities", {}
            )

            if predicted_class not in CLASS_NAMES:
                raise ValueError(
                    f"Unknown predicted class: {predicted_class}"
                )

            y_true.append(true_class)
            y_pred.append(predicted_class)

            row = {
                "filename": image_path.name,
                "image_path": str(image_path),
                "true_class": true_class,
                "predicted_class": predicted_class,
                "correct": predicted_class == true_class,
                "confidence": confidence,
            }

            for class_name in CLASS_NAMES:
                row[f"prob_{class_name}"] = probabilities.get(
                    class_name, ""
                )

            row["tampered_area_percentage"] = localization.get(
                "tampered_area_percentage", ""
            )

            row["mean_probability"] = localization.get(
                "mean_probability", ""
            )

            row["maximum_probability"] = localization.get(
                "maximum_probability", ""
            )

            classification_rows.append(row)

            print(f"  True:       {true_class}")
            print(f"  Predicted:  {predicted_class}")
            print(f"  Confidence: {confidence:.4f}")
            print(
                "  Mask area:  "
                f"{localization.get('tampered_area_percentage', 'N/A')}%"
            )

            # ------------------------------------------------
            # LOCALIZATION EVALUATION
            # ------------------------------------------------

            # AI-generated images are not evaluated as localized
            # tampering unless a meaningful localized ground-truth
            # mask has explicitly been defined for that task.
            if true_class == "ai_generated":
                continue

            predicted_mask = to_numpy_mask(localization["mask"])
            predicted_mask = predicted_mask.astype(bool)

            mask_row = {
                "filename": image_path.name,
                "true_class": true_class,
                "predicted_area_percentage": (
                    float(predicted_mask.mean()) * 100
                ),
            }

            if true_class == "real":
                # A real image should ideally have no positive pixels.
                mask_row.update({
                    "iou": "",
                    "dice": "",
                    "precision": "",
                    "recall": "",
                    "false_positive_area_percentage": (
                        float(predicted_mask.mean()) * 100
                    ),
                    "mask_status": "real_image_false_positive_measure",
                })

                localization_rows.append(mask_row)
                continue

            # Copy-move and splicing require ground-truth masks.
            ground_truth_path = (
                MASK_DIR
                / true_class
                / f"{image_path.stem}.png"
            )

            if not ground_truth_path.exists():
                print(
                    "  [WARNING] Missing ground-truth mask: "
                    f"{ground_truth_path}"
                )

                mask_row.update({
                    "iou": "",
                    "dice": "",
                    "precision": "",
                    "recall": "",
                    "false_positive_area_percentage": "",
                    "mask_status": "missing_ground_truth",
                })

                localization_rows.append(mask_row)
                continue

            ground_truth_mask = load_ground_truth_mask(
                ground_truth_path,
                predicted_mask.shape,
            )

            metrics = calculate_localization_metrics(
                predicted_mask,
                ground_truth_mask,
            )

            mask_row.update(metrics)
            mask_row["false_positive_area_percentage"] = ""
            mask_row["mask_status"] = "evaluated"

            localization_rows.append(mask_row)

            print(
                f"  Localization IoU:  {metrics['iou']:.4f}"
            )
            print(
                f"  Localization Dice: {metrics['dice']:.4f}"
            )

        except Exception as error:
            print(f"  [ERROR] {error}")

            failed_rows.append({
                "filename": image_path.name,
                "image_path": str(image_path),
                "true_class": true_class,
                "error": str(error),
                "traceback": traceback.format_exc(),
            })

    elapsed = time.perf_counter() - start_time

    # ========================================================
    # CLASSIFICATION METRICS
    # ========================================================

    if not y_true:
        raise RuntimeError(
            "No images were evaluated successfully. "
            "Check the pipeline errors above."
        )

    accuracy = accuracy_score(y_true, y_pred)

    macro_precision = precision_score(
        y_true,
        y_pred,
        labels=CLASS_NAMES,
        average="macro",
        zero_division=0,
    )

    macro_recall = recall_score(
        y_true,
        y_pred,
        labels=CLASS_NAMES,
        average="macro",
        zero_division=0,
    )

    macro_f1 = f1_score(
        y_true,
        y_pred,
        labels=CLASS_NAMES,
        average="macro",
        zero_division=0,
    )

    report = classification_report(
        y_true,
        y_pred,
        labels=CLASS_NAMES,
        output_dict=True,
        zero_division=0,
    )

    matrix = confusion_matrix(
        y_true,
        y_pred,
        labels=CLASS_NAMES,
    )

    # Save confusion matrix.
    fig, ax = plt.subplots(figsize=(8, 6))

    sns.heatmap(
        matrix,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=CLASS_NAMES,
        yticklabels=CLASS_NAMES,
        ax=ax,
    )

    ax.set_xlabel("Predicted class")
    ax.set_ylabel("True class")
    ax.set_title("ForenXNet Classification Confusion Matrix")

    plt.tight_layout()

    confusion_path = OUTPUT_DIR / "confusion_matrix.png"
    fig.savefig(confusion_path, dpi=200)
    plt.close(fig)

    # ========================================================
    # SAVE CSV FILES
    # ========================================================

    def save_csv(filename, rows):
        if not rows:
            return

        # Include keys from all rows, even if some fields are blank.
        fieldnames = list(
            dict.fromkeys(
                key
                for row in rows
                for key in row.keys()
            )
        )

        with open(
            OUTPUT_DIR / filename,
            "w",
            newline="",
            encoding="utf-8-sig",
        ) as file:
            writer = csv.DictWriter(
                file,
                fieldnames=fieldnames,
                extrasaction="ignore",
            )
            writer.writeheader()
            writer.writerows(rows)

    save_csv("classification_predictions.csv", classification_rows)
    save_csv("localization_metrics.csv", localization_rows)
    save_csv("failed_images.csv", failed_rows)

    # ========================================================
    # LOCALIZATION SUMMARY
    # ========================================================

    evaluated_masks = [
        row for row in localization_rows
        if row.get("mask_status") == "evaluated"
    ]

    real_rows = [
        row for row in localization_rows
        if row.get("mask_status")
        == "real_image_false_positive_measure"
    ]

    localization_summary = {}

    for class_name in ("copy_move", "splicing"):

        class_rows = [
            row for row in evaluated_masks
            if row["true_class"] == class_name
        ]

        localization_summary[class_name] = {
            "evaluated_images": len(class_rows),
            "mean_iou": (
                float(np.mean([row["iou"] for row in class_rows]))
                if class_rows else None
            ),
            "mean_dice": (
                float(np.mean([row["dice"] for row in class_rows]))
                if class_rows else None
            ),
            "mean_precision": (
                float(np.mean([
                    row["precision"] for row in class_rows
                ]))
                if class_rows else None
            ),
            "mean_recall": (
                float(np.mean([
                    row["recall"] for row in class_rows
                ]))
                if class_rows else None
            ),
        }

    localization_summary["real"] = {
        "evaluated_images": len(real_rows),
        "mean_false_positive_area_percentage": (
            float(np.mean([
                row["false_positive_area_percentage"]
                for row in real_rows
            ]))
            if real_rows else None
        ),
    }

    # ========================================================
    # SAVE JSON SUMMARY
    # ========================================================

    summary = {
        "images_found": len(samples),
        "images_evaluated": len(y_true),
        "failed_images": len(failed_rows),
        "accuracy": float(accuracy),
        "macro_precision": float(macro_precision),
        "macro_recall": float(macro_recall),
        "macro_f1": float(macro_f1),
        "classification_report": report,
        "confusion_matrix": matrix.tolist(),
        "class_order": CLASS_NAMES,
        "localization": localization_summary,
        "elapsed_seconds": elapsed,
        "notes": [
            "Results describe only the supplied evaluation set.",
            "AI-generated images are not scored for localized "
            "tampering by default.",
            "Copy-move/splicing localization metrics require "
            "matching ground-truth masks.",
            "Missing masks are not counted as localization successes "
            "or failures.",
        ],
    }

    summary_path = OUTPUT_DIR / "evaluation_summary.json"

    with open(summary_path, "w", encoding="utf-8") as file:
        json.dump(summary, file, indent=4)

    # ========================================================
    # PRINT FINAL RESULTS
    # ========================================================

    print("\n" + "=" * 65)
    print("CLASSIFICATION RESULTS")
    print("=" * 65)

    print(f"Images found:      {len(samples)}")
    print(f"Evaluated:         {len(y_true)}")
    print(f"Failed:            {len(failed_rows)}")
    print(f"Accuracy:          {accuracy:.4f}")
    print(f"Macro Precision:   {macro_precision:.4f}")
    print(f"Macro Recall:      {macro_recall:.4f}")
    print(f"Macro F1:          {macro_f1:.4f}")

    print("\nPer-class metrics:")

    for class_name in CLASS_NAMES:
        metrics = report[class_name]

        print(
            f"{class_name:15s} "
            f"Precision={metrics['precision']:.4f} "
            f"Recall={metrics['recall']:.4f} "
            f"F1={metrics['f1-score']:.4f} "
            f"Support={int(metrics['support'])}"
        )

    print("\nConfusion matrix (true rows, predicted columns):")
    print(matrix)

    print("\n" + "=" * 65)
    print("LOCALIZATION RESULTS")
    print("=" * 65)

    for class_name, metrics in localization_summary.items():
        print(f"\n{class_name}:")

        for metric_name, value in metrics.items():
            if isinstance(value, float):
                print(f"  {metric_name}: {value:.4f}")
            else:
                print(f"  {metric_name}: {value}")

    print("\n" + "=" * 65)
    print("OUTPUT FILES")
    print("=" * 65)

    print(f"Summary:       {summary_path}")
    print(f"Predictions:   {OUTPUT_DIR / 'classification_predictions.csv'}")
    print(f"Localization:  {OUTPUT_DIR / 'localization_metrics.csv'}")
    print(f"Confusion:     {confusion_path}")
    print(f"Failed images: {OUTPUT_DIR / 'failed_images.csv'}")
    print(f"Elapsed time:  {elapsed:.2f} seconds")


if __name__ == "__main__":
    main()