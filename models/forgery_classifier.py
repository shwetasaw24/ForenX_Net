from pathlib import Path

import torch
import torch.nn as nn

from torchvision import transforms
from torchvision.models import efficientnet_b0

from config.settings import (
    DEVICE,
    FORGERY_MODEL_PATH,
)

from services.preprocessing_service import (
    ForensicPreprocessor
)


class ForgeryClassifier:

    def __init__(
        self,
        model_path=FORGERY_MODEL_PATH,
        device=DEVICE
    ):

        self.device = device

        self.model_path = Path(
            model_path
        )

        if not self.model_path.exists():

            raise FileNotFoundError(
                f"Forgery model not found:\n"
                f"{self.model_path}"
            )

        # =====================================================
        # LOAD CHECKPOINT
        # =====================================================

        checkpoint = torch.load(
            self.model_path,
            map_location=self.device,
            weights_only=True
        )

        self.classes = checkpoint[
            "classes"
        ]

        self.image_size = checkpoint[
            "image_size"
        ]

        # =====================================================
        # FORENSIC PREPROCESSOR
        # =====================================================

        self.preprocessor = (
            ForensicPreprocessor(
                target_size=self.image_size
            )
        )

        # =====================================================
        # CREATE EXACT TRAINED ARCHITECTURE
        # =====================================================

        self.model = efficientnet_b0(
            weights=None
        )

        self.model.classifier[1] = nn.Linear(
            self.model.classifier[1].in_features,
            len(self.classes)
        )

        # =====================================================
        # LOAD TRAINED WEIGHTS
        # =====================================================

        self.model.load_state_dict(
            checkpoint[
                "model_state_dict"
            ]
        )

        self.model = self.model.to(
            self.device
        )

        self.model.eval()

        # =====================================================
        # MODEL NORMALIZATION
        # =====================================================

        self.transform = transforms.Compose([

            transforms.ToTensor(),

            transforms.Normalize(

                mean=[
                    0.485,
                    0.456,
                    0.406
                ],

                std=[
                    0.229,
                    0.224,
                    0.225
                ]
            )
        ])


    # =========================================================
    # PREDICT
    # =========================================================

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

        # =====================================================
        # FORENSIC PREPROCESSING
        # =====================================================

        preprocessing_result = (
            self.preprocessor.process(
                image_path
            )
        )

        image = preprocessing_result[
            "image"
        ]

        # =====================================================
        # CONVERT TO TENSOR
        # =====================================================

        image_tensor = self.transform(
            image
        )

        image_tensor = image_tensor.unsqueeze(
            0
        )

        image_tensor = image_tensor.to(
            self.device
        )

        # =====================================================
        # INFERENCE
        # =====================================================

        with torch.no_grad():

            outputs = self.model(
                image_tensor
            )

            probabilities = torch.softmax(
                outputs,
                dim=1
            )[0]

            predicted_index = torch.argmax(
                probabilities
            ).item()

        # =====================================================
        # RESULTS
        # =====================================================

        predicted_class = self.classes[
            predicted_index
        ]

        confidence = probabilities[
            predicted_index
        ].item()

        class_probabilities = {

            self.classes[i]:
                probabilities[i].item()

            for i in range(
                len(self.classes)
            )
        }

        # =====================================================
        # RETURN
        # =====================================================

        return {

            "predicted_class":
                predicted_class,

            "confidence":
                confidence,

            "class_probabilities":
                class_probabilities,

            "preprocessing": {

                "original_size":
                    preprocessing_result[
                        "original_size"
                    ],

                "processed_size":
                    preprocessing_result[
                        "processed_size"
                    ]
            }
        }