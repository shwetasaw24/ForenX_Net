from pathlib import Path

from services.metadata_service import (
    MetadataService
)

from services.metadata_analyzer import (
    MetadataAnalyzer
)

from models.forgery_classifier import (
    ForgeryClassifier
)

from models.tamper_localizer import (
    TamperLocalizer
)

from services.visualization_service import (
    VisualizationService
)

from services.evidence_fusion import (
    EvidenceFusion
)


class ForenXNetPipeline:

    def __init__(self):

        print(
            "Initializing ForenXNet..."
        )

        # =====================================================
        # METADATA
        # =====================================================

        self.metadata_service = (
            MetadataService()
        )

        self.evidence_fusion = (
            EvidenceFusion()
        )

        # =====================================================
        # FORGERY CLASSIFICATION
        # =====================================================

        self.forgery_classifier = (
            ForgeryClassifier()
        )

        # =====================================================
        # TAMPER LOCALIZATION
        # =====================================================

        self.tamper_localizer = (
            TamperLocalizer()
        )

        # =====================================================
        # VISUALIZATION
        # =====================================================

        self.visualization_service = (
            VisualizationService()
        )

        print(
            "ForenXNet initialized successfully."
        )

    # =========================================================
    # ANALYZE IMAGE
    # =========================================================

    def analyze(
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
        # 1. METADATA ANALYSIS
        # =====================================================

        raw_metadata = (
            self.metadata_service.extract_raw(
                image_path
            )
        )

        metadata_analyzer = (
            MetadataAnalyzer(
                raw_metadata
            )
        )

        metadata_result = (
            metadata_analyzer.analyze()
        )


        
        # =====================================================
        # 2. FORGERY CLASSIFICATION
        # =====================================================

        classification_result = (
            self.forgery_classifier.predict(
                image_path
            )
        )

        # =====================================================
        # 3. TAMPER LOCALIZATION
        # =====================================================

        localization_result = (
            self.tamper_localizer.predict(
                image_path
            )
        )

        # =====================================================
        # 4. LOCALIZATION STATISTICS
        # =====================================================

        mask = (
            localization_result[
                "mask"
            ]
        )

        probability_mask = (
            localization_result[
                "probability_mask"
            ]
        )

        threshold = (
            localization_result[
                "threshold"
            ]
        )

        total_pixels = (
            mask.numel()
        )

        tampered_pixels = (
            mask.sum().item()
        )

        tampered_area_percentage = (
            tampered_pixels /
            total_pixels
        ) * 100

        mean_probability = (
            probability_mask
            .mean()
            .item()
        )

        maximum_probability = (
            probability_mask
            .max()
            .item()
        )

        # =====================================================
        # 6. EVIDENCE FUSION
        # =====================================================

        fusion_result = (
            self.evidence_fusion.fuse(
            
                metadata_result=metadata_result,

                raw_metadata=raw_metadata,

                classification_result=
                    classification_result,

                localization_result={
                
                    "tampered_area_percentage":
                        tampered_area_percentage,

                    "mean_probability":
                        mean_probability,

                    "maximum_probability":
                        maximum_probability,

                    "threshold":
                        threshold
                }
            )
        )

        # =====================================================
        # 5. VISUALIZATION DATA
        # =====================================================

        visualization_result = (
            self.visualization_service.generate(
                image_path=image_path,

                probability_mask=
                    probability_mask,

                threshold=
                    threshold
            )
        )

        # =====================================================
        # 6. FINAL RESULT
        # =====================================================

        result = {

            # -------------------------------------------------
            # IMAGE
            # -------------------------------------------------

            "image": {

                "path":
                    str(image_path),

                "filename":
                    image_path.name
            },

            # -------------------------------------------------
            # METADATA
            # -------------------------------------------------

            "metadata":
                metadata_result,

            "raw_metadata":
                raw_metadata,

            # -------------------------------------------------
            # FORGERY CLASSIFICATION
            # -------------------------------------------------

            "forgery_classification": {

                "predicted_class":
                    classification_result[
                        "predicted_class"
                    ],

                "confidence":
                    classification_result[
                        "confidence"
                    ],

                "class_probabilities":
                    classification_result[
                        "class_probabilities"
                    ]
            },

            # -------------------------------------------------
            # LOCALIZATION
            # -------------------------------------------------

            "localization": {

                "tampered_area_percentage":
                    round(
                        tampered_area_percentage,
                        2
                    ),

                "mean_probability":
                    round(
                        mean_probability,
                        6
                    ),

                "maximum_probability":
                    round(
                        maximum_probability,
                        6
                    ),

                "threshold":
                    threshold,

                "mask":
                    mask,

                "probability_mask":
                    probability_mask
            },

            "evidence_fusion":
                fusion_result,

            # -------------------------------------------------
            # VISUALIZATION
            # -------------------------------------------------

            "visualization": {

                "available":
                    True,

                "original":
                    visualization_result[
                        "original"
                    ],

                "heatmap":
                    visualization_result[
                        "heatmap"
                    ],

                "binary_mask":
                    visualization_result[
                        "binary_mask"
                    ],

                "overlay":
                    visualization_result[
                        "overlay"
                    ]
            },

            # -------------------------------------------------
            # SOURCE CAMERA
            # -------------------------------------------------

            "source_camera": {

                "available":
                    False,

                "status":
                    "SOURCE_CAMERA_MODULE_NOT_AVAILABLE",

                "prediction":
                    None,

                "confidence":
                    None
            }
        }

        return result