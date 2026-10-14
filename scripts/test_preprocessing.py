from pathlib import Path

from services.preprocessing_service import (
    ForensicPreprocessor
)


def main():

    print("=" * 70)
    print("FORENXNET FORENSIC PREPROCESSING TEST")
    print("=" * 70)


    # =========================================================
    # INPUT
    # =========================================================

    image_path = Path(
        r"C:\Users\Shweeta\OneDrive\Documents\MAJORPROJECT\evaluation_dataset\copy_move\jpg format\1dda2c31-d980-4955-84a0-5a5b6b61a997.jpg"
    )


    print(
        "\nInput image:"
    )

    print(
        image_path
    )


    # =========================================================
    # INITIALIZE
    # =========================================================

    print(
        "\nInitializing preprocessor..."
    )

    preprocessor = (
        ForensicPreprocessor(
            target_size=224
        )
    )

    print(
        "Preprocessor initialized."
    )


    # =========================================================
    # PROCESS
    # =========================================================

    print(
        "\nProcessing image..."
    )

    result = (
        preprocessor.process(
            image_path
        )
    )


    # =========================================================
    # RESULTS
    # =========================================================

    print(
        "\n" + "-" * 70
    )

    print(
        "PREPROCESSING RESULTS"
    )

    print(
        "-" * 70
    )


    print(
        "Original size:",
        result[
            "original_size"
        ]
    )


    print(
        "Processed size:",
        result[
            "processed_size"
        ]
    )


    print(
        "Color mode:",
        result[
            "image"
        ].mode
    )


    # =========================================================
    # SAVE TEST IMAGE
    # =========================================================

    output_path = Path(
        "data/samples/preprocessed_test.jpg"
    )

    result[
        "image"
    ].save(
        output_path,
        quality=95
    )


    print(
        "\nSaved processed image:"
    )

    print(
        output_path
    )


    print(
        "\n" + "=" * 70
    )

    print(
        "PREPROCESSING TEST COMPLETE"
    )

    print(
        "=" * 70
    )


if __name__ == "__main__":

    main()