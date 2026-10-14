from pathlib import Path

from config.settings import SAMPLES_DIR

from services.metadata_service import MetadataService


def main():

    image_path = SAMPLES_DIR / "test.jpg"

    print("=" * 70)
    print("FORENXNET METADATA TEST")
    print("=" * 70)

    print(f"\nImage: {image_path}")

    # Check image
    if not image_path.exists():
        print("\nERROR: Test image not found.")
        return

    # Initialize metadata service
    service = MetadataService()

    print("\nExtracting metadata...")

    metadata = service.extract_raw(image_path)

    print("\nMetadata extraction successful!")

    print(
        f"\nTotal metadata fields: {len(metadata)}"
    )

    print("\n" + "-" * 70)
    print("IMPORTANT METADATA")
    print("-" * 70)

    fields = [
        "Make",
        "Model",
        "CameraModelName",
        "Software",
        "DateTimeOriginal",
        "ISO",
        "FocalLength",
        "ExposureTime",
        "FNumber",
        "ImageWidth",
        "ImageHeight",
        "Orientation"
    ]

    for field in fields:

        value = metadata.get(field)

        # ExifTool may return grouped keys
        # such as IFD0:Make or ExifIFD:ISO
        if value is None:

            for key, val in metadata.items():

                if key.endswith(
                    ":" + field
                ):

                    value = val
                    break

        print(
            f"{field:20s}: {value}"
        )

    print("\n" + "-" * 70)
    print("ALL METADATA")
    print("-" * 70)

    for key, value in metadata.items():

        print(
            f"{key:40s}: {value}"
        )

    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()