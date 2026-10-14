from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from PIL import Image


class VisualizationService:

    def __init__(self):

        print(
            "Visualization service initialized."
        )

    # =========================================================
    # LOAD IMAGE
    # =========================================================

    def load_image(self, image_path):

        image_path = Path(
            image_path
        )

        image = Image.open(
            image_path
        ).convert("RGB")

        return np.array(
            image
        )

    # =========================================================
    # PREPARE PROBABILITY MASK
    # =========================================================

    def prepare_probability_mask(
        self,
        probability_mask
    ):

        if hasattr(
            probability_mask,
            "detach"
        ):

            probability_mask = (
                probability_mask
                .detach()
                .cpu()
                .numpy()
            )

        probability_mask = np.squeeze(
            probability_mask
        )

        probability_mask = np.clip(
            probability_mask,
            0.0,
            1.0
        )

        return probability_mask

    # =========================================================
    # RESIZE MASK
    # =========================================================

    def resize_mask(
        self,
        probability_mask,
        image_shape
    ):

        height = image_shape[0]
        width = image_shape[1]

        mask_image = Image.fromarray(
            (
                probability_mask * 255
            ).astype(
                np.uint8
            )
        )

        mask_image = mask_image.resize(
            (width, height),
            Image.Resampling.BILINEAR
        )

        return (
            np.array(
                mask_image
            ) / 255.0
        )

    # =========================================================
    # BINARY MASK
    # =========================================================

    def create_binary_mask(
        self,
        probability_mask,
        threshold
    ):

        return (
            probability_mask >= threshold
        )

    # =========================================================
    # OVERLAY
    # =========================================================

    def create_overlay(
        self,
        image,
        binary_mask,
        alpha=0.45
    ):

        overlay = (
            image.astype(
                np.float32
            )
        )

        red_layer = np.zeros_like(
            overlay
        )

        red_layer[:, :, 0] = 255

        mask = binary_mask.astype(
            bool
        )

        overlay[mask] = (
            (1 - alpha)
            * overlay[mask]
            +
            alpha
            * red_layer[mask]
        )

        return np.clip(
            overlay,
            0,
            255
        ).astype(
            np.uint8
        )

    # =========================================================
    # GENERATE VISUALIZATION DATA
    # =========================================================

    def generate(
        self,
        image_path,
        probability_mask,
        threshold
    ):

        image = self.load_image(
            image_path
        )

        probability_mask = (
            self.prepare_probability_mask(
                probability_mask
            )
        )

        probability_mask = (
            self.resize_mask(
                probability_mask,
                image.shape
            )
        )

        binary_mask = (
            self.create_binary_mask(
                probability_mask,
                threshold
            )
        )

        overlay = (
            self.create_overlay(
                image,
                binary_mask
            )
        )

        return {

            "original":
                image,

            "heatmap":
                probability_mask,

            "probability_mask":
                probability_mask,

            "binary_mask":
                binary_mask,

            "overlay":
                overlay,

            "threshold":
                threshold
        }

    # =========================================================
    # SHOW FORENSIC DASHBOARD
    # =========================================================

    def show_dashboard(
        self,
        image_path,
        probability_mask,
        threshold,
        class_probabilities=None,
        predicted_class=None,
        confidence=None
    ):

        data = self.generate(
            image_path,
            probability_mask,
            threshold
        )

        original = data[
            "original"
        ]

        probability = data[
            "probability_mask"
        ]

        binary_mask = data[
            "binary_mask"
        ]

        overlay = data[
            "overlay"
        ]

        # =====================================================
        # STATISTICS
        # =====================================================

        total_pixels = (
            binary_mask.size
        )

        tampered_pixels = (
            binary_mask.sum()
        )

        tampered_percentage = (
            tampered_pixels /
            total_pixels
        ) * 100

        mean_probability = (
            probability.mean()
        )

        maximum_probability = (
            probability.max()
        )

        # =====================================================
        # DASHBOARD
        # =====================================================

        fig, axes = plt.subplots(
            2,
            3,
            figsize=(18, 11)
        )

        fig.suptitle(
            "ForenXNet Forensic Visualization",
            fontsize=18
        )

        # -----------------------------------------------------
        # 1. ORIGINAL
        # -----------------------------------------------------

        axes[0, 0].imshow(
            original
        )

        axes[0, 0].set_title(
            "Original Image"
        )

        axes[0, 0].axis(
            "off"
        )

        # -----------------------------------------------------
        # 2. HEATMAP
        # -----------------------------------------------------

        heatmap = axes[0, 1].imshow(
            probability,
            cmap="jet",
            vmin=0,
            vmax=1
        )

        axes[0, 1].set_title(
            "Tamper Probability Heatmap"
        )

        axes[0, 1].axis(
            "off"
        )

        fig.colorbar(
            heatmap,
            ax=axes[0, 1],
            fraction=0.046,
            pad=0.04
        )

        # -----------------------------------------------------
        # 3. BINARY MASK
        # -----------------------------------------------------

        axes[0, 2].imshow(
            binary_mask,
            cmap="gray"
        )

        axes[0, 2].set_title(
            f"Binary Tamper Mask "
            f"(Threshold = {threshold})"
        )

        axes[0, 2].axis(
            "off"
        )

        # -----------------------------------------------------
        # 4. OVERLAY
        # -----------------------------------------------------

        axes[1, 0].imshow(
            overlay
        )

        axes[1, 0].set_title(
            "Tamper Localization Overlay"
        )

        axes[1, 0].axis(
            "off"
        )

        # -----------------------------------------------------
        # 5. CLASSIFICATION
        # -----------------------------------------------------

        if class_probabilities:

            classes = list(
                class_probabilities.keys()
            )

            probabilities = [
                class_probabilities[c]
                for c in classes
            ]

            probabilities = [
                p * 100
                if p <= 1
                else p
                for p in probabilities
            ]

            axes[1, 1].bar(
                classes,
                probabilities
            )

            axes[1, 1].set_title(
                "Forgery Classification"
            )

            axes[1, 1].set_ylabel(
                "Probability (%)"
            )

            axes[1, 1].set_ylim(
                0,
                100
            )

            axes[1, 1].tick_params(
                axis="x",
                rotation=20
            )

        else:

            axes[1, 1].text(
                0.5,
                0.5,
                "Classification data unavailable",
                ha="center",
                va="center"
            )

            axes[1, 1].axis(
                "off"
            )

        # -----------------------------------------------------
        # 6. FORENSIC METRICS
        # -----------------------------------------------------

        axes[1, 2].axis(
            "off"
        )

        if confidence is None:

            confidence_text = "N/A"

        elif confidence <= 1:

            confidence_text = (
                f"{confidence * 100:.2f}%"
            )

        else:

            confidence_text = (
                f"{confidence:.2f}%"
            )

        metrics_text = (

            "FORENSIC METRICS\n\n"

            f"Predicted class:\n"
            f"  {predicted_class or 'N/A'}\n\n"

            f"Classification confidence:\n"
            f"  {confidence_text}\n\n"

            f"Tampered area:\n"
            f"  {tampered_percentage:.2f}%\n\n"

            f"Mean probability:\n"
            f"  {mean_probability:.4f}\n\n"

            f"Maximum probability:\n"
            f"  {maximum_probability:.4f}\n\n"

            f"Threshold:\n"
            f"  {threshold}"
        )

        axes[1, 2].text(
            0.05,
            0.95,
            metrics_text,
            verticalalignment="top",
            fontsize=12
        )

        plt.tight_layout(
            rect=[
                0,
                0,
                1,
                0.95
            ]
        )

        plt.show()

        return data