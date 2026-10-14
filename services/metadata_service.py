import json
import subprocess
from pathlib import Path

from config.settings import EXIFTOOL_PATH


class MetadataService:

    def __init__(self):
        self.exiftool_path = Path(EXIFTOOL_PATH)

        if not self.exiftool_path.exists():
            raise FileNotFoundError(
                f"ExifTool not found at:\n"
                f"{self.exiftool_path}"
            )

    def extract_raw(self, image_path):
        """
        Extract complete raw metadata using ExifTool.

        Returns:
            dict: Raw metadata returned by ExifTool.
        """

        image_path = Path(image_path)

        if not image_path.exists():
            raise FileNotFoundError(
                f"Image not found:\n{image_path}"
            )

        result = subprocess.run(
            [
                str(self.exiftool_path),
                "-j",
                "-G1",
                "-a",
                "-s",
                str(image_path)
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )

        if result.returncode != 0:
            raise RuntimeError(
                "ExifTool failed:\n"
                + result.stderr
            )

        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "Unable to parse ExifTool output."
            ) from exc

        if not data:
            return {}

        return data[0]