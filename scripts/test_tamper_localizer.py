from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

from PIL import Image

from config.settings import (
    SAMPLES_DIR,
)

from models.tamper_localizer import (
    TamperLocalizer,
)


def main():

    image_path = (
        "C:\\Users\\Shweeta\\OneDrive\\Documents\\MAJORPROJECT\\ForenXNet\\data\\splicing\\casia_Tp_D_CNN_M_B_nat10139_nat00097_11948.jpg"
    )

    output_dir = Path(
        "data/outputs"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    print("=" * 70)
    print("FORENXNET U-NET TAMPER LOCALIZATION")
    print("=" * 70)

    print("\nImage:")
    print(image_path)

    # =========================================================
    # LOAD MODEL
    # =========================================================

    print("\nLoading U-Net...")

    localizer = TamperLocalizer()

    print("U-Net loaded successfully.")

    print(
        "\nDevice:",
        localizer.device
    )

    print(
        "Threshold:",
        localizer.threshold
    )

    # =========================================================
    # LOAD ORIGINAL IMAGE
    # =========================================================

    original_image = Image.open(
        image_path
    ).convert("RGB")

    # =========================================================
    # RUN LOCALIZATION
    # =========================================================

    print("\nRunning localization...")

    result = localizer.predict(
        image_path
    )

    mask = result["mask"]

    probability_mask = result[
        "probability_mask"
    ]

    # =========================================================
    # STATISTICS
    # =========================================================

    total_pixels = mask.numel()

    tampered_pixels = mask.sum().item()

    tampered_percentage = (
        tampered_pixels /
        total_pixels
    ) * 100

    mean_probability = (
        probability_mask.mean().item()
    )

    max_probability = (
        probability_mask.max().item()
    )

    print("\n" + "=" * 70)
    print("LOCALIZATION RESULTS")
    print("=" * 70)

    print(
        "\nOriginal image size:",
        result["original_size"]
    )

    print(
        "Model input size:",
        result["input_size"]
    )

    print(
        "Threshold:",
        result["threshold"]
    )

    print(
        "\nTampered pixels:",
        f"{tampered_pixels:.0f}"
    )

    print(
        "Total pixels:",
        total_pixels
    )

    print(
        "Predicted tampered area:",
        f"{tampered_percentage:.2f}%"
    )

    print(
        "Mean mask probability:",
        f"{mean_probability:.4f}"
    )

    print(
        "Maximum mask probability:",
        f"{max_probability:.4f}"
    )

    # =========================================================
    # CONVERT MASK TO NUMPY
    # =========================================================

    mask_np = mask.numpy()

    probability_np = (
        probability_mask.numpy()
    )

    image_np = np.array(
        original_image
    )

    # =========================================================
    # SAVE BINARY MASK
    # =========================================================

    mask_uint8 = (
        mask_np * 255
    ).astype(
        np.uint8
    )

    mask_image = Image.fromarray(
        mask_uint8
    )

    mask_path = (
        output_dir /
        "tamper_mask.png"
    )

    mask_image.save(
        mask_path
    )

    # =========================================================
    # CREATE OVERLAY
    # =========================================================

    # Resize binary mask to original image size

    mask_full = Image.fromarray(
        mask_uint8
    ).resize(
        original_image.size
    )

    mask_full_np = np.array(
        mask_full
    )

    # Create overlay

    overlay = image_np.copy()

    tampered_region = (
        mask_full_np > 0
    )

    # Highlight detected region

    overlay[
        tampered_region
    ] = [
        255,
        0,
        0
    ]

    # Blend with original

    blended = (
        0.65 * image_np +
        0.35 * overlay
    ).astype(
        np.uint8
    )

    overlay_image = Image.fromarray(
        blended
    )

    overlay_path = (
        output_dir /
        "tamper_overlay.png"
    )

    overlay_image.save(
        overlay_path
    )

    # =========================================================
    # SAVE PROBABILITY MAP
    # =========================================================

    probability_image = (
        probability_np * 255
    ).clip(
        0,
        255
    ).astype(
        np.uint8
    )

    probability_image = Image.fromarray(
        probability_image
    )

    probability_path = (
        output_dir /
        "tamper_probability.png"
    )

    probability_image.save(
        probability_path
    )

    # =========================================================
    # DISPLAY
    # =========================================================

    plt.figure(
        figsize=(15, 5)
    )

    plt.subplot(
        1,
        3,
        1
    )

    plt.imshow(
        original_image
    )

    plt.title(
        "Original Image"
    )

    plt.axis(
        "off"
    )


    plt.subplot(
        1,
        3,
        2
    )

    plt.imshow(
        mask_np,
        cmap="gray"
    )

    plt.title(
        f"Predicted Mask\n"
        f"{tampered_percentage:.2f}%"
    )

    plt.axis(
        "off"
    )


    plt.subplot(
        1,
        3,
        3
    )

    plt.imshow(
        blended
    )

    plt.title(
        "Tamper Overlay"
    )

    plt.axis(
        "off"
    )


    plt.tight_layout()

    visualization_path = (
        output_dir /
        "tamper_visualization.png"
    )

    plt.savefig(
        visualization_path,
        dpi=150,
        bbox_inches="tight"
    )

    plt.close()

    # =========================================================
    # COMPLETE
    # =========================================================

    print(
        "\nSaved files:"
    )

    print(
        f"  Mask:          {mask_path}"
    )

    print(
        f"  Probability:   {probability_path}"
    )

    print(
        f"  Overlay:       {overlay_path}"
    )

    print(
        f"  Visualization: {visualization_path}"
    )

    print(
        "\n" + "=" * 70
    )

    print(
        "U-NET LOCALIZATION COMPLETE"
    )

    print(
        "=" * 70
    )


if __name__ == "__main__":
    main()