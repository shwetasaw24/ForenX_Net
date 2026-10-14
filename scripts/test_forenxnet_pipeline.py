from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.forenxnet_pipeline import (
    ForenXNetPipeline
)


def format_percentage(value):

    if value is None:
        return "N/A"

    return f"{float(value) * 100:.2f}%"


def main():

    print("=" * 75)
    print("FORENXNET COMPLETE FORENSIC ANALYSIS")
    print("=" * 75)

    # =========================================================
    # INPUT IMAGEs
    # =========================================================

    image_path = Path(
        "C:\\Users\\Shweeta\\OneDrive\\Documents\\MAJORPROJECT\\ForenXNet\\data\\evaluation\\ai_generated\\804ac3c4-d961-4fb1-b8e7-e23edcd535d3.png"
    )


    print("\nInput image:")
    print(image_path)

    if not image_path.exists():

        raise FileNotFoundError(
            f"Image not found:\n{image_path}"
        )

    # =========================================================
    # INITIALIZE
    # =========================================================

    print("\nInitializing ForenXNet...")

    pipeline = ForenXNetPipeline()

    print("ForenXNet initialized successfully.")

    # =========================================================
    # COMPLETE ANALYSIS
    # =========================================================

    print("\nRunning complete forensic analysis...")

    result = pipeline.analyze(
        image_path
    )

    # =========================================================
    # 1. METADATA ANALYSIS
    # =========================================================

    metadata = result[
        "metadata"
    ]

    raw_metadata = result.get(
        "raw_metadata",
        {}
    )

    print(
        "\n" + "=" * 75
    )

    print(
        "1. METADATA FORENSIC ANALYSIS"
    )

    print(
        "=" * 75
    )

    print(
        "Status:",
        metadata[
            "metadata_status"
        ]
    )

    print(
        "Completeness:",
        f"{metadata['metadata_completeness']:.2f}%"
    )

    print(
        "Camera metadata:",
        metadata[
            "camera_metadata_available"
        ]
    )

    print(
        "GPS metadata:",
        metadata[
            "gps_metadata_available"
        ]
    )

    # =========================================================
    # ALL RAW METADATA
    # =========================================================

    print(
        "\n" + "-" * 75
    )

    print(
        "ALL METADATA PRESENT IN IMAGE"
    )

    print(
        "-" * 75
    )

    print(
        f"Total metadata fields: "
        f"{len(raw_metadata)}"
    )

    if len(raw_metadata) == 0:

        print(
            "No metadata fields detected."
        )

    else:

        for key, value in raw_metadata.items():

            print(
                f"{str(key):48s}: {value}"
            )

    # =========================================================
    # 2. FORGERY CLASSIFICATION
    # =========================================================

    classification = result[
        "forgery_classification"
    ]

    print(
        "\n" + "=" * 75
    )

    print(
        "2. FORGERY CLASSIFICATION"
    )

    print(
        "=" * 75
    )

    predicted_class = classification[
        "predicted_class"
    ]

    classifier_confidence = classification[
        "confidence"
    ]

    print(
        "Model prediction:",
        predicted_class
    )

    print(
        "Model confidence:",
        format_percentage(
            classifier_confidence
        )
    )

    print(
        "\nClass probabilities:"
    )

    for (
        class_name,
        probability
    ) in classification[
        "class_probabilities"
    ].items():

        print(
            f"  {class_name:20s}: "
            f"{format_percentage(probability)}"
        )

    # =========================================================
    # 3. TAMPER LOCALIZATION
    # =========================================================

    localization = result[
        "localization"
    ]

    print(
        "\n" + "=" * 75
    )

    print(
        "3. TAMPER LOCALIZATION"
    )

    print(
        "=" * 75
    )

    print(
        "Tampered area:",
        f"{localization['tampered_area_percentage']:.2f}%"
    )

    print(
        "Mean probability:",
        f"{localization['mean_probability']:.6f}"
    )

    print(
        "Maximum probability:",
        f"{localization['maximum_probability']:.6f}"
    )

    print(
        "Threshold:",
        localization[
            "threshold"
        ]
    )

    # =========================================================
    # 4. SOURCE CAMERA IDENTIFICATION
    # =========================================================

    source_camera = result[
        "source_camera"
    ]

    print(
        "\n" + "=" * 75
    )

    print(
        "4. SOURCE CAMERA IDENTIFICATION"
    )

    print(
        "=" * 75
    )

    print(
        "Available:",
        source_camera[
            "available"
        ]
    )

    print(
        "Status:",
        source_camera[
            "status"
        ]
    )

    if source_camera.get(
        "prediction"
    ) is not None:

        print(
            "Prediction:",
            source_camera[
                "prediction"
            ]
        )

    if source_camera.get(
        "confidence"
    ) is not None:

        print(
            "Confidence:",
            format_percentage(
                source_camera[
                    "confidence"
                ]
            )
        )

    # =========================================================
    # 5. EVIDENCE FUSION
    # =========================================================

    fusion = result.get(
        "evidence_fusion"
    )

    print(
        "\n" + "=" * 75
    )

    print(
        "5. FORENXNET EVIDENCE FUSION"
    )

    print(
        "=" * 75
    )

    if fusion is None:

        print(
            "Evidence fusion result unavailable."
        )

    else:

        verdict = fusion.get(
            "verdict",
            "UNCERTAIN"
        )

        final_class = fusion.get(
            "final_class",
            "unknown"
        )

        fusion_confidence = fusion.get(
            "confidence",
            0.0
        )

        reason = fusion.get(
            "reason",
            "No explanation available."
        )

        evidence = fusion.get(
            "evidence",
            {}
        )

        # -----------------------------------------------------
        # FINAL FORENSIC VERDICT
        # -----------------------------------------------------

        print(
            "\nFINAL FORENSIC VERDICT"
        )

        print(
            "-" * 75
        )

        print(
            "Verdict:",
            verdict
        )

        print(
            "Final class:",
            final_class
        )

        print(
            "Fusion confidence:",
            format_percentage(
                fusion_confidence
            )
        )

        print(
            "\nReason:"
        )

        print(
            reason
        )

        # -----------------------------------------------------
        # EVIDENCE CONSISTENCY
        # -----------------------------------------------------

        print(
            "\nEvidence consistency:"
        )

        print(
            evidence.get(
                "evidence_consistent",
                False
            )
        )

        # -----------------------------------------------------
        # AI METADATA EVIDENCE
        # -----------------------------------------------------

        ai_metadata = evidence.get(
            "ai_metadata",
            {}
        )

        print(
            "\nAI metadata evidence:"
        )

        print(
            "Detected:",
            ai_metadata.get(
                "detected",
                False
            )
        )

        matches = ai_metadata.get(
            "matches",
            []
        )

        if matches:

            print(
                "\nAI metadata matches:"
            )

            for match in matches:

                print(
                    f"  Field   : "
                    f"{match.get('field')}"
                )

                print(
                    f"  Value   : "
                    f"{match.get('value')}"
                )

                print(
                    f"  Keyword : "
                    f"{match.get('keyword')}"
                )

        # -----------------------------------------------------
        # CLASSIFIER SUPPORT
        # -----------------------------------------------------

        print(
            "\nClassifier support:"
        )

        print(
            evidence.get(
                "classifier_support",
                False
            )
        )

        # -----------------------------------------------------
        # LOCALIZATION SUPPORT
        # -----------------------------------------------------

        print(
            "Localization support:"
        )

        print(
            evidence.get(
                "localization_support",
                False
            )
        )

    # =========================================================
    # 6. FORENSIC VISUALIZATION
    # =========================================================

    print(
        "\n" + "=" * 75
    )

    print(
        "6. FORENSIC VISUALIZATION"
    )

    print(
        "=" * 75
    )

    visualization = result.get(
        "visualization"
    )

    if (
        visualization
        and
        visualization.get(
            "available",
            False
        )
    ):

        print(
            "Displaying forensic dashboard..."
        )

        pipeline.visualization_service.show_dashboard(

            image_path=image_path,

            probability_mask=
                localization[
                    "probability_mask"
                ],

            threshold=
                localization[
                    "threshold"
                ],

            class_probabilities=
                classification[
                    "class_probabilities"
                ],

            predicted_class=
                classification[
                    "predicted_class"
                ],

            confidence=
                classification[
                    "confidence"
                ]
        )

    else:

        print(
            "Visualization unavailable."
        )

    # =========================================================
    # COMPLETE
    # =========================================================

    print(
        "\n" + "=" * 75
    )

    print(
        "FORENXNET FORENSIC ANALYSIS COMPLETE"
    )

    print(
        "=" * 75
    )


if __name__ == "__main__":

    main()