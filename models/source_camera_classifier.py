from pathlib import Path

import torch
import torch.nn as nn
from PIL import Image
from torchvision import models, transforms
from models.camera_device_mapping import get_device_name


class SourceCameraClassifier:
    """
    ForenXNet Source Camera Identification (SCI).

    Architecture:
        ResNet-50

    Open-set rejection:
        Maximum Softmax Probability (MSP)

    The model predicts a camera only when the maximum
    softmax probability meets the calibrated threshold.
    """

    def __init__(
        self,
        checkpoint_path=None,
        threshold=0.988544,
        device=None,
    ):
        project_root = Path(__file__).resolve().parent.parent

        if checkpoint_path is None:
            checkpoint_path = (
                project_root
                / "weights"
                / "best_openset_resnet50.pth"
            )

        self.checkpoint_path = Path(checkpoint_path)

        self.device = torch.device(
            device
            if device is not None
            else (
                "cuda"
                if torch.cuda.is_available()
                else "cpu"
            )
        )

        if not self.checkpoint_path.is_file():
            raise FileNotFoundError(
                "SCI checkpoint not found: "
                f"{self.checkpoint_path}"
            )

        # Load checkpoint.
        # weights_only=False is needed for checkpoints
        # containing metadata dictionaries in some PyTorch versions.
        # Only load a checkpoint you trust.
        try:
            checkpoint = torch.load(
                self.checkpoint_path,
                map_location=self.device,
                weights_only=True,
            )
        except TypeError:
            # Compatibility with older PyTorch versions.
            checkpoint = torch.load(
                self.checkpoint_path,
                map_location=self.device,
            )

        if not isinstance(checkpoint, dict):
            raise ValueError(
                "Unexpected SCI checkpoint format."
            )

        state_dict = checkpoint.get(
            "model_state_dict",
            checkpoint.get("state_dict"),
        )

        if state_dict is None:
            raise KeyError(
                "Checkpoint does not contain "
                "'model_state_dict' or 'state_dict'."
            )

        # Read mappings saved during training
        self.class_to_idx = checkpoint.get("class_to_idx")
        saved_idx_to_class = checkpoint.get("idx_to_class")

        if not self.class_to_idx:
            raise ValueError(
                "Missing class_to_idx in SCI checkpoint."
            )

        # Normalize class_to_idx: {"D01": 0, ...}
        self.class_to_idx = {
            str(label): int(index)
            for label, index in self.class_to_idx.items()
        }

        # Reconstruct the reverse mapping from class_to_idx.
        # This avoids assuming the stored idx_to_class format.
        self.idx_to_class = {
            index: label
            for label, index in self.class_to_idx.items()
        }

        # Validate the optional saved reverse mapping.
        if saved_idx_to_class is not None:
            if all(
                str(key).isdigit()
                for key in saved_idx_to_class.keys()
            ):
                saved_reverse = {
                    int(index): str(label)
                    for index, label in saved_idx_to_class.items()
                }
            else:
                # Also support {"D01": 0, ...}
                saved_reverse = {
                    int(index): str(label)
                    for label, index in saved_idx_to_class.items()
                }

            if saved_reverse != self.idx_to_class:
                raise ValueError(
                    "Inconsistent camera-class mappings "
                    "in the SCI checkpoint."
                )

        self.num_classes = len(self.class_to_idx)

        if set(self.idx_to_class.keys()) != set(
            range(self.num_classes)
        ):
            raise ValueError(
                "Camera class indices must be contiguous "
                "from 0 to num_classes - 1."
            )

        if set(self.idx_to_class) != set(range(self.num_classes)):
            raise ValueError(
                "Camera class indices must be contiguous "
                "from 0 to num_classes - 1."
            )

        # Prefer the threshold stored with the trained checkpoint.
        self.threshold = float(
            checkpoint.get("msp_threshold", threshold)
        )

        # Build the same ResNet-50 architecture used for training.
        self.model = models.resnet50(weights=None)

        self.model.fc = nn.Linear(
            self.model.fc.in_features,
            self.num_classes,
        )

        self.model.load_state_dict(state_dict)

        self.model.to(self.device)
        self.model.eval()

        # Match the training/evaluation preprocessing.
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225],
            ),
        ])

        print(
            "SCI model loaded successfully | "
            f"Device: {self.device} | "
            f"Camera classes: {self.num_classes} | "
            f"MSP threshold: {self.threshold:.6f}"
        )

    def predict(self, image_path):
        """
        Predict the source-camera class for an image.

        Returns a dictionary suitable for the
        ForenXNet pipeline and report.
        """

        image_path = Path(image_path)

        if not image_path.is_file():
            raise FileNotFoundError(
                f"SCI image not found: {image_path}"
            )

        try:
            with Image.open(image_path) as image:
                image = image.convert("RGB")
                input_tensor = self.transform(image).unsqueeze(0)

        except Exception as exc:
            raise ValueError(
                f"SCI could not read image: {image_path}"
            ) from exc

        input_tensor = input_tensor.to(self.device)

        with torch.inference_mode():
            logits = self.model(input_tensor)
            probabilities = torch.softmax(logits, dim=1)

            confidence_tensor, predicted_index_tensor = (
                probabilities.max(dim=1)
            )

        confidence = float(confidence_tensor.item())
        predicted_index = int(predicted_index_tensor.item())

        candidate_camera = self.idx_to_class[predicted_index]

        is_unknown = confidence < self.threshold

        # Do not report a camera attribution when rejected.
        predicted_camera = (
            None if is_unknown else candidate_camera
        )

        class_probabilities = {
            self.idx_to_class[index]: float(probability)
            for index, probability in enumerate(
                probabilities[0].cpu().tolist()
            )
        }

        return {
            "available": True,
            "module": "source_camera_identification",
            "status": (
                "unknown_camera"
                if is_unknown
                else "prediction_available"
            ),
            "predicted_camera": predicted_camera,
            "candidate_camera": candidate_camera,
            "confidence": confidence,
            "open_set_score": confidence,
            "threshold": self.threshold,
            "is_unknown": is_unknown,
            "model": "resnet50_msp",
            "class_probabilities": class_probabilities,
            "limitations": [
                "Experimental closed-set camera classifier.",
                "Unknown rejection is imperfect.",
                "Prediction is not proof of image provenance.",
                "Prediction does not establish image authenticity.",
            ],
            "predicted_device_name": get_device_name(predicted_camera),
            "candidate_device_name": get_device_name(candidate_camera),
        }