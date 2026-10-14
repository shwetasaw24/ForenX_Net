from pathlib import Path

from models.tamper_localizer import (
    TamperLocalizer
)

from models.forgery_classifier import (
    ForgeryClassifier
)

from services.visualization_service import (
    VisualizationService
)


def main():

    print("=" * 70)
    print("FORENXNET VISUALIZATION TEST")
    print("=" * 70)

    # =========================================================
    # IMAGE
    # =========================================================

    image_path = Path(
        r"C:\Users\Shweeta\OneDrive\Documents\MAJORPROJECT\ForenXNet\data\copy_move\comodof_011_F_JC2.jpg"
    )

    print(
        "\nImage:"
    )

    print(
        image_path
    )

    if not image_path.exists():

        raise FileNotFoundError(
            f"Image not found:\n{image_path}"
        )

    # =========================================================
    # FORGERY CLASSIFIER
    # =========================================================

    print(
        "\nLoading forgery classifier..."
    )

    classifier = (
        ForgeryClassifier()
    )

    print(
        "Forgery classifier loaded."
    )

    print(
        "\nRunning classification..."
    )

    classification = (
        classifier.predict(
            image_path
        )
    )

    # =========================================================
    # TAMPER LOCALIZER
    # =========================================================

    print(
        "\nLoading tamper localizer..."
    )

    localizer = (
        TamperLocalizer()
    )

    print(
        "Tamper localizer loaded."
    )

    print(
        "\nRunning localization..."
    )

    localization = (
        localizer.predict(
            image_path
        )
    )

    # =========================================================
    # VISUALIZATION
    # =========================================================

    print(
        "\nGenerating visualization..."
    )

    visualizer = (
        VisualizationService()
    )

    visualizer.show_dashboard(

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

    print(
        "\n" + "=" * 70
    )

    print(
        "VISUALIZATION TEST COMPLETE"
    )

    print(
        "=" * 70
    )


if __name__ == "__main__":

    main()