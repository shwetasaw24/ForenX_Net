from pathlib import Path

from PIL import Image, ImageOps


class ForensicPreprocessor:

    def __init__(
        self,
        target_size=224
    ):

        self.target_size = target_size


    # =========================================================
    # VALIDATE IMAGE
    # =========================================================

    def validate(
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

        try:

            with Image.open(
                image_path
            ) as image:

                image.verify()

        except Exception as e:

            raise ValueError(
                f"Invalid or corrupted image:\n"
                f"{image_path}\n"
                f"Reason: {e}"
            )


    # =========================================================
    # LOAD IMAGE
    # =========================================================

    def load(
        self,
        image_path
    ):

        self.validate(
            image_path
        )

        image = Image.open(
            image_path
        )

        # -----------------------------------------------------
        # Correct EXIF orientation
        # -----------------------------------------------------

        image = ImageOps.exif_transpose(
            image
        )

        # -----------------------------------------------------
        # Convert to RGB
        # -----------------------------------------------------

        image = image.convert(
            "RGB"
        )

        return image


    # =========================================================
    # RESIZE WHILE PRESERVING ASPECT RATIO
    # =========================================================

    def resize_preserve_aspect(
        self,
        image
    ):

        image = ImageOps.contain(

            image,

            (
                self.target_size,
                self.target_size
            ),

            method=Image.Resampling.LANCZOS
        )

        # -----------------------------------------------------
        # Create square RGB canvas
        # -----------------------------------------------------

        canvas = Image.new(

            "RGB",

            (
                self.target_size,
                self.target_size
            ),

            (0, 0, 0)
        )

        # -----------------------------------------------------
        # Center image
        # -----------------------------------------------------

        x = (
            self.target_size -
            image.width
        ) // 2

        y = (
            self.target_size -
            image.height
        ) // 2

        canvas.paste(
            image,
            (
                x,
                y
            )
        )

        return canvas


    # =========================================================
    # COMPLETE PREPROCESSING
    # =========================================================

    def process(
        self,
        image_path
    ):

        image = self.load(
            image_path
        )

        original_size = (
            image.width,
            image.height
        )

        processed_image = (
            self.resize_preserve_aspect(
                image
            )
        )

        return {

            "image":
                processed_image,

            "original_size":
                original_size,

            "processed_size":
                (
                    self.target_size,
                    self.target_size
                )
        }