from typing import Any


class MetadataAnalyzer:

    # ---------------------------------------------------------
    # Camera / device identification metadata
    # ---------------------------------------------------------

    CAMERA_FIELDS = [
        "Make",
        "Model",
        "CameraModelName",
        "LensModel",
        "SerialNumber"
    ]

    # ---------------------------------------------------------
    # Image capture metadata
    # ---------------------------------------------------------

    CAPTURE_FIELDS = [
        "DateTimeOriginal",
        "ExposureTime",
        "FNumber",
        "ISO",
        "FocalLength"
    ]

    # ---------------------------------------------------------
    # Editing / processing metadata
    # ---------------------------------------------------------

    SOFTWARE_FIELDS = [
        "Software",
        "CreatorTool",
        "ProcessingSoftware"
    ]

    # ---------------------------------------------------------
    # Location metadata
    # ---------------------------------------------------------

    GPS_FIELDS = [
        "GPSLatitude",
        "GPSLongitude"
    ]


    def __init__(
        self,
        metadata: dict[str, Any]
    ):

        self.metadata = metadata


    # =========================================================
    # FIELD ACCESS
    # =========================================================

    def _get_field(
        self,
        field: str
    ):

        # Direct field
        if field in self.metadata:

            return self.metadata[field]

        # ExifTool grouped fields
        #
        # Examples:
        #
        # IFD0:Make
        # IFD0:Model
        # ExifIFD:ISO
        # ExifIFD:FNumber
        #

        for key, value in self.metadata.items():

            if key.endswith(
                ":" + field
            ):

                return value

        return None


    # =========================================================
    # CHECK WHETHER FIELD CONTAINS USABLE INFORMATION
    # =========================================================

    def _field_available(
        self,
        field: str
    ) -> bool:

        value = self._get_field(
            field
        )

        if value is None:
            return False

        value_string = str(
            value
        ).strip()

        if value_string == "":
            return False

        if value_string.lower() in {
            "none",
            "unknown",
            "null"
        }:
            return False

        return True


    # =========================================================
    # CHECK FIELD GROUP
    # =========================================================

    def _group_available(
        self,
        fields
    ) -> bool:

        return any(
            self._field_available(field)
            for field in fields
        )


    # =========================================================
    # ANALYSIS
    # =========================================================

    def analyze(self):

        # -----------------------------------------------------
        # Extract grouped metadata
        # -----------------------------------------------------

        camera_metadata = {
            field:
                self._get_field(field)
            for field in self.CAMERA_FIELDS
        }

        capture_metadata = {
            field:
                self._get_field(field)
            for field in self.CAPTURE_FIELDS
        }

        software_metadata = {
            field:
                self._get_field(field)
            for field in self.SOFTWARE_FIELDS
        }


        # -----------------------------------------------------
        # Availability
        # -----------------------------------------------------

        camera_available = (
            self._group_available(
                self.CAMERA_FIELDS
            )
        )

        capture_available = (
            self._group_available(
                self.CAPTURE_FIELDS
            )
        )

        software_available = (
            self._group_available(
                self.SOFTWARE_FIELDS
            )
        )

        gps_available = (
            self._group_available(
                self.GPS_FIELDS
            )
        )


        # -----------------------------------------------------
        # Metadata completeness
        #
        # This is NOT a forgery probability.
        #
        # It represents the proportion of selected
        # metadata fields that are populated.
        # -----------------------------------------------------

        relevant_fields = (
            self.CAMERA_FIELDS
            + self.CAPTURE_FIELDS
            + self.SOFTWARE_FIELDS
            + self.GPS_FIELDS
        )

        total_relevant_fields = len(
            relevant_fields
        )

        available_relevant_fields = sum(
            self._field_available(field)
            for field in relevant_fields
        )

        if total_relevant_fields > 0:

            completeness = (
                available_relevant_fields
                / total_relevant_fields
            ) * 100.0

        else:

            completeness = 0.0


        # -----------------------------------------------------
        # Metadata status
        # -----------------------------------------------------

        if camera_available:

            metadata_status = (
                "CAMERA_METADATA_AVAILABLE"
            )

        elif (
            software_available
            or capture_available
            or gps_available
        ):

            metadata_status = (
                "METADATA_PRESENT_CAMERA_UNAVAILABLE"
            )

        else:

            metadata_status = (
                "METADATA_ABSENT_OR_MINIMAL"
            )


        # -----------------------------------------------------
        # Forensic indicators
        #
        # These are EVIDENCE FLAGS.
        #
        # They are NOT conclusions that the image is forged.
        # -----------------------------------------------------

        indicators = []


        if camera_available:

            indicators.append(
                "CAMERA_METADATA_AVAILABLE"
            )

        else:

            indicators.append(
                "CAMERA_MODEL_UNAVAILABLE"
            )


        if software_available:

            indicators.append(
                "SOFTWARE_METADATA_PRESENT"
            )


        if capture_available:

            indicators.append(
                "CAPTURE_PARAMETERS_PRESENT"
            )


        if gps_available:

            indicators.append(
                "GPS_METADATA_PRESENT"
            )


        if len(self.metadata) == 0:

            indicators.append(
                "NO_METADATA_EXTRACTED"
            )


        # -----------------------------------------------------
        # Return structured forensic metadata
        # -----------------------------------------------------

        return {

            # Basic metadata statistics
            "metadata_field_count":
                len(self.metadata),

            "metadata_completeness":
                round(
                    completeness,
                    2
                ),

            "metadata_status":
                metadata_status,


            # Availability flags
            "camera_metadata_available":
                camera_available,

            "capture_metadata_available":
                capture_available,

            "software_metadata_available":
                software_available,

            "gps_metadata_available":
                gps_available,


            # Structured metadata
            "camera_metadata":
                camera_metadata,

            "capture_metadata":
                capture_metadata,

            "software_metadata":
                software_metadata,


            # Forensic evidence flags
            "forensic_indicators":
                indicators
        }