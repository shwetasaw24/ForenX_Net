from pathlib import Path

import torch
import torch.nn as nn

from PIL import Image

from torchvision import transforms

from config.settings import (
    DEVICE,
    UNET_MODEL_PATH,
    LOCALIZATION_IMAGE_SIZE,
)


# ============================================================
# DOUBLE CONV
# ============================================================

class DoubleConv(nn.Module):

    def __init__(
        self,
        in_c,
        out_c
    ):

        super().__init__()

        self.conv = nn.Sequential(

            nn.Conv2d(
                in_c,
                out_c,
                kernel_size=3,
                padding=1
            ),

            nn.ReLU(
                inplace=True
            ),

            nn.Conv2d(
                out_c,
                out_c,
                kernel_size=3,
                padding=1
            ),

            nn.ReLU(
                inplace=True
            )
        )


    def forward(self, x):

        return self.conv(x)


# ============================================================
# U-NET
# ============================================================

class UNet(nn.Module):

    def __init__(self):

        super().__init__()

        # Encoder

        self.d1 = DoubleConv(
            3,
            64
        )

        self.p1 = nn.MaxPool2d(
            2
        )


        self.d2 = DoubleConv(
            64,
            128
        )

        self.p2 = nn.MaxPool2d(
            2
        )


        self.d3 = DoubleConv(
            128,
            256
        )

        self.p3 = nn.MaxPool2d(
            2
        )


        self.d4 = DoubleConv(
            256,
            512
        )

        self.p4 = nn.MaxPool2d(
            2
        )


        # Bottleneck

        self.b = DoubleConv(
            512,
            1024
        )


        # Decoder

        self.u1 = nn.ConvTranspose2d(
            1024,
            512,
            2,
            2
        )

        self.c1 = DoubleConv(
            1024,
            512
        )


        self.u2 = nn.ConvTranspose2d(
            512,
            256,
            2,
            2
        )

        self.c2 = DoubleConv(
            512,
            256
        )


        self.u3 = nn.ConvTranspose2d(
            256,
            128,
            2,
            2
        )

        self.c3 = DoubleConv(
            256,
            128
        )


        self.u4 = nn.ConvTranspose2d(
            128,
            64,
            2,
            2
        )

        self.c4 = DoubleConv(
            128,
            64
        )


        # Output

        self.out = nn.Conv2d(
            64,
            1,
            1
        )


    def forward(
        self,
        x
    ):

        # Encoder

        d1 = self.d1(x)

        d2 = self.d2(
            self.p1(d1)
        )

        d3 = self.d3(
            self.p2(d2)
        )

        d4 = self.d4(
            self.p3(d3)
        )


        # Bottleneck

        b = self.b(
            self.p4(d4)
        )


        # Decoder

        u1 = self.u1(b)

        u1 = torch.cat(
            [u1, d4],
            dim=1
        )

        u1 = self.c1(u1)


        u2 = self.u2(u1)

        u2 = torch.cat(
            [u2, d3],
            dim=1
        )

        u2 = self.c2(u2)


        u3 = self.u3(u2)

        u3 = torch.cat(
            [u3, d2],
            dim=1
        )

        u3 = self.c3(u3)


        u4 = self.u4(u3)

        u4 = torch.cat(
            [u4, d1],
            dim=1
        )

        u4 = self.c4(u4)


        return self.out(u4)


# ============================================================
# TAMPER LOCALIZER
# ============================================================

class TamperLocalizer:

    def __init__(
        self,
        model_path=UNET_MODEL_PATH,
        device=DEVICE,
        threshold=0.3
    ):

        self.device = device

        self.model_path = Path(
            model_path
        )

        self.threshold = threshold

        # ----------------------------------------------------
        # Check checkpoint
        # ----------------------------------------------------

        if not self.model_path.exists():

            raise FileNotFoundError(
                f"U-Net model not found:\n"
                f"{self.model_path}"
            )


        # ----------------------------------------------------
        # Create exact architecture
        # ----------------------------------------------------

        self.model = UNet()


        # ----------------------------------------------------
        # Load state_dict
        # ----------------------------------------------------

        state_dict = torch.load(
            self.model_path,
            map_location=self.device,
            weights_only=True
        )

        self.model.load_state_dict(
            state_dict
        )


        # ----------------------------------------------------
        # Device
        # ----------------------------------------------------

        self.model = self.model.to(
            self.device
        )

        self.model.eval()


        # ----------------------------------------------------
        # Image preprocessing
        # ----------------------------------------------------

        self.transform = transforms.Compose([

            transforms.Resize(
                (
                    LOCALIZATION_IMAGE_SIZE,
                    LOCALIZATION_IMAGE_SIZE
                )
            ),

            transforms.ToTensor()
        ])


    # ========================================================
    # PREDICT MASK
    # ========================================================

    def predict(
        self,
        image_path
    ):

        image_path = Path(
            image_path
        )

        if not image_path.exists():

            raise FileNotFoundError(
                f"Image not found:\n"
                f"{image_path}"
            )


        # ----------------------------------------------------
        # Load image
        # ----------------------------------------------------

        image = Image.open(
            image_path
        ).convert("RGB")


        original_size = image.size


        # ----------------------------------------------------
        # Transform
        # ----------------------------------------------------

        image_tensor = self.transform(
            image
        )

        image_tensor = image_tensor.unsqueeze(
            0
        )

        image_tensor = image_tensor.to(
            self.device
        )


        # ----------------------------------------------------
        # Model inference
        # ----------------------------------------------------

        with torch.no_grad():

            logits = self.model(
                image_tensor
            )

            probability = torch.sigmoid(
                logits
            )

            binary_mask = (
                probability >
                self.threshold
            ).float()


        # ----------------------------------------------------
        # Remove batch/channel dimensions
        # ----------------------------------------------------

        probability = (
            probability[0, 0]
            .cpu()
        )

        binary_mask = (
            binary_mask[0, 0]
            .cpu()
        )


        return {

            "mask": binary_mask,

            "probability_mask":
                probability,

            "input_size":
                (
                    LOCALIZATION_IMAGE_SIZE,
                    LOCALIZATION_IMAGE_SIZE
                ),

            "original_size":
                original_size,

            "threshold":
                self.threshold
        }