from config.settings import (
    SAMPLES_DIR
)

from models.forgery_classifier import (
    ForgeryClassifier
)


def main():

    image_path = (
        r"C:\\Users\\Shweeta\\OneDrive\\Documents\\MAJORPROJECT\\ForenXNet\\data\\evaluation\\ai_generated\\b4f0364c-105a-4808-8001-ba863b8ee8b0.png"
    )

    print("=" * 70)
    print("FORENXNET EFFICIENTNET-B0 FORGERY CLASSIFIER")
    print("=" * 70)

    print("\nImage:")
    print(image_path)

    # =========================================================
    # LOAD MODEL
    # =========================================================

    print("\nLoading EfficientNet-B0...")

    classifier = ForgeryClassifier()

    print("Model loaded successfully.")

    print(
        "\nDevice:",
        classifier.device
    )

    print(
        "Classes:",
        classifier.classes
    )

    print(
        "Input size:",
        classifier.image_size
    )

    # =========================================================
    # PREDICTION
    # =========================================================

    print("\nRunning inference...")

    result = classifier.predict(
        image_path
    )

    # =========================================================
    # DISPLAY RESULT
    # =========================================================

    print("\n" + "=" * 70)

    print(
        "Predicted Class:",
        result[
            "predicted_class"
        ]
    )

    print(
        "Confidence:",
        f"{result['confidence'] * 100:.2f}%"
    )

    print("=" * 70)

    print(
        "\nClass Probabilities:"
    )

    for class_name, probability in (
        result[
            "class_probabilities"
        ].items()
    ):

        print(
            f"{class_name:15s}: "
            f"{probability * 100:.2f}%"
        )

    print(
        "\n" + "=" * 70
    )


if __name__ == "__main__":

    main()