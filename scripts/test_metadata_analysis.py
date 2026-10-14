from config.settings import SAMPLES_DIR

from services.metadata_service import MetadataService
from services.metadata_analyzer import MetadataAnalyzer


def main():

    image_path = SAMPLES_DIR / "test1.jpg"

    print("=" * 70)
    print("FORENXNET METADATA FORENSIC ANALYSIS")
    print("=" * 70)

    # =========================================================
    # STEP 1 — CHECK IMAGE
    # =========================================================

    if not image_path.exists():

        print("\nERROR: Image not found:")
        print(image_path)

        return

    # =========================================================
    # STEP 2 — EXTRACT RAW METADATA
    # =========================================================

    service = MetadataService()

    metadata = service.extract_raw(
        image_path
    )

    # =========================================================
    # STEP 3 — ANALYZE METADATA
    # =========================================================

    analyzer = MetadataAnalyzer(
        metadata
    )

    result = analyzer.analyze()

    # =========================================================
    # STEP 4 — BASIC INFORMATION
    # =========================================================

    print("\nMetadata Fields:")

    print(
        result["metadata_field_count"]
    )

    print("\nMetadata Status:")

    print(
        result["metadata_status"]
    )

    print("\nMetadata Completeness:")

    print(
        f"{result['metadata_completeness']:.2f}%"
    )

    # =========================================================
    # STEP 5 — AVAILABILITY
    # =========================================================

    print("\nAvailability:")

    print(
        "Camera Metadata   :",
        result["camera_metadata_available"]
    )

    print(
        "Capture Metadata  :",
        result["capture_metadata_available"]
    )

    print(
        "Software Metadata :",
        result["software_metadata_available"]
    )

    print(
        "GPS Metadata      :",
        result["gps_metadata_available"]
    )

    # =========================================================
    # STEP 6 — FORENSIC INDICATORS
    # =========================================================

    print("\nForensic Indicators:")

    indicators = result[
        "forensic_indicators"
    ]

    if indicators:

        for indicator in indicators:

            print(
                f"  - {indicator}"
            )

    else:

        print(
            "  None"
        )

    # =========================================================
    # STEP 7 — CAMERA METADATA
    # =========================================================

    print("\nCamera Metadata:")

    for key, value in (
        result["camera_metadata"].items()
    ):

        print(
            f"  {key:20s}: {value}"
        )

    # =========================================================
    # STEP 8 — CAPTURE METADATA
    # =========================================================

    print("\nCapture Metadata:")

    for key, value in (
        result["capture_metadata"].items()
    ):

        print(
            f"  {key:20s}: {value}"
        )

    # =========================================================
    # STEP 9 — SOFTWARE METADATA
    # =========================================================

    print("\nSoftware Metadata:")

    for key, value in (
        result["software_metadata"].items()
    ):

        print(
            f"  {key:20s}: {value}"
        )

    # =========================================================
    # COMPLETE
    # =========================================================

    print("\n" + "=" * 70)

    print(
        "METADATA ANALYSIS COMPLETE"
    )

    print(
        "=" * 70
    )


if __name__ == "__main__":

    main()