class EvidenceFusion:

    # =========================================================
    # CONFIGURATION
    # =========================================================

    TAMPER_AREA_THRESHOLD = 0.5

    LOCALIZATION_PROBABILITY_THRESHOLD = 0.30

    CLASSIFICATION_CONFIDENCE_THRESHOLD = 0.70

    AI_CLASSIFICATION_THRESHOLD = 0.70

    AI_METADATA_KEYWORDS = [

        "midjourney",
        "dall-e",
        "dalle",
        "stable diffusion",
        "stable-diffusion",
        "adobe firefly",
        "firefly",
        "leonardo ai",
        "leonardo.ai",
        "ideogram",
        "bing image creator",
        "copilot image creator",
        "canva ai",
        "generative fill",
        "generative ai",
        "Open Ai"
    ]

    # =========================================================
    # MAIN FUSION
    # =========================================================

    def fuse(
        self,
        metadata_result,
        raw_metadata,
        classification_result,
        localization_result
    ):

        predicted_class = (
            classification_result[
                "predicted_class"
            ]
        )

        classification_confidence = (
            classification_result[
                "confidence"
            ]
        )

        class_probabilities = (
            classification_result[
                "class_probabilities"
            ]
        )

        tampered_area = (
            localization_result[
                "tampered_area_percentage"
            ]
        )

        mean_probability = (
            localization_result[
                "mean_probability"
            ]
        )

        maximum_probability = (
            localization_result[
                "maximum_probability"
            ]
        )

        # =====================================================
        # 1. METADATA AI EVIDENCE
        # =====================================================

        ai_metadata_evidence = (
            self.detect_ai_metadata(
                raw_metadata
            )
        )

        # =====================================================
        # 2. LOCALIZATION EVIDENCE
        # =====================================================

        localization_supports_tampering = (

            tampered_area
            >=
            self.TAMPER_AREA_THRESHOLD

            and

            maximum_probability
            >=
            self.LOCALIZATION_PROBABILITY_THRESHOLD
        )

        localization_supports_no_tampering = (

            tampered_area
            <
            self.TAMPER_AREA_THRESHOLD

            and

            maximum_probability
            <
            self.LOCALIZATION_PROBABILITY_THRESHOLD
        )

        # =====================================================
        # 3. CLASSIFICATION EVIDENCE
        # =====================================================

        classification_confident = (

            classification_confidence
            >=
            self.CLASSIFICATION_CONFIDENCE_THRESHOLD
        )

        # =====================================================
        # 4. AI-GENERATED DECISION
        # =====================================================

        ai_probability = (
            class_probabilities.get(
                "ai_generated",
                0.0
            )
        )

        ai_classifier_support = (

            ai_probability
            >=
            self.AI_CLASSIFICATION_THRESHOLD
        )

        # Strongest AI evidence:
        # explicit AI-generation metadata.

        if ai_metadata_evidence["detected"]:

            final_class = "ai_generated"

            verdict = (
                "AI_GENERATED"
            )

            confidence = max(
                ai_probability,
                0.90
            )

            reason = (
                "AI-generation metadata evidence "
                "was detected."
            )

            return self._build_result(
                verdict=verdict,
                final_class=final_class,
                confidence=confidence,
                reason=reason,
                ai_metadata_evidence=
                    ai_metadata_evidence,
                classification_support=
                    ai_classifier_support,
                localization_support=
                    localization_supports_tampering,
                evidence_consistent=True
            )

        # If classifier strongly supports AI,
        # use it as model evidence.

        if ai_classifier_support:

            final_class = "ai_generated"

            verdict = (
                "AI_GENERATED"
            )

            confidence = ai_probability

            reason = (
                "Forgery classifier strongly "
                "supports AI-generated content."
            )

            return self._build_result(
                verdict=verdict,
                final_class=final_class,
                confidence=confidence,
                reason=reason,
                ai_metadata_evidence=
                    ai_metadata_evidence,
                classification_support=True,
                localization_support=
                    localization_supports_tampering,
                evidence_consistent=True
            )

        # =====================================================
        # 5. COPY-MOVE
        # =====================================================

        copy_move_probability = (
            class_probabilities.get(
                "copy_move",
                0.0
            )
        )

        if (

            predicted_class
            == "copy_move"

            and

            classification_confident

            and

            localization_supports_tampering
        ):

            return self._build_result(

                verdict=
                    "COPY_MOVE_TAMPERING",

                final_class=
                    "copy_move",

                confidence=
                    copy_move_probability,

                reason=(
                    "Classifier and tamper "
                    "localization agree on "
                    "copy-move manipulation."
                ),

                ai_metadata_evidence=
                    ai_metadata_evidence,

                classification_support=True,

                localization_support=True,

                evidence_consistent=True
            )

        # =====================================================
        # 6. SPLICING
        # =====================================================

        splicing_probability = (
            class_probabilities.get(
                "splicing",
                0.0
            )
        )

        if (

            predicted_class
            == "splicing"

            and

            classification_confident

            and

            localization_supports_tampering
        ):

            return self._build_result(

                verdict=
                    "SPLICING_TAMPERING",

                final_class=
                    "splicing",

                confidence=
                    splicing_probability,

                reason=(
                    "Classifier and tamper "
                    "localization agree on "
                    "splicing manipulation."
                ),

                ai_metadata_evidence=
                    ai_metadata_evidence,

                classification_support=True,

                localization_support=True,

                evidence_consistent=True
            )

        # =====================================================
        # 7. CLASSIFIER / LOCALIZATION CONFLICT
        # =====================================================

        if (

            predicted_class
            in [
                "copy_move",
                "splicing"
            ]

            and

            classification_confident

            and

            localization_supports_no_tampering
        ):

            return self._build_result(

                verdict=
                    "NO_SIGNIFICANT_TAMPERING_DETECTED",

                final_class=
                    "real",

                confidence=
                    1.0 -
                    classification_confidence,

                reason=(
                    "Forgery classifier predicted "
                    f"{predicted_class}, but tamper "
                    "localization found no significant "
                    "tampered region."
                ),

                ai_metadata_evidence=
                    ai_metadata_evidence,

                classification_support=True,

                localization_support=False,

                evidence_consistent=False
            )

        # =====================================================
        # 8. REAL
        # =====================================================

        real_probability = (
            class_probabilities.get(
                "real",
                0.0
            )
        )

        if (

            predicted_class
            == "real"

            and

            classification_confident

            and

            localization_supports_no_tampering
        ):

            return self._build_result(

                verdict=
                    "REAL",

                final_class=
                    "real",

                confidence=
                    real_probability,

                reason=(
                    "Classifier predicts real and "
                    "no significant tampered region "
                    "was localized."
                ),

                ai_metadata_evidence=
                    ai_metadata_evidence,

                classification_support=True,

                localization_support=False,

                evidence_consistent=True
            )

        # =====================================================
        # 9. UNCERTAIN
        # =====================================================

        return self._build_result(

            verdict=
                "UNCERTAIN",

            final_class=
                predicted_class,

            confidence=
                classification_confidence,

            reason=(
                "Available forensic evidence is "
                "insufficient or inconsistent "
                "for a definitive verdict."
            ),

            ai_metadata_evidence=
                ai_metadata_evidence,

            classification_support=
                classification_confident,

            localization_support=
                localization_supports_tampering,

            evidence_consistent=False
        )

    # =========================================================
    # AI METADATA DETECTION
    # =========================================================

    def detect_ai_metadata(
        self,
        raw_metadata
    ):

        matches = []

        for key, value in raw_metadata.items():

            if value is None:
                continue

            value_string = (
                str(value)
                .lower()
            )

            for keyword in (
                self.AI_METADATA_KEYWORDS
            ):

                if keyword in value_string:

                    matches.append({

                        "field":
                            key,

                        "value":
                            value,

                        "keyword":
                            keyword
                    })

        return {

            "detected":
                len(matches) > 0,

            "matches":
                matches
        }

    # =========================================================
    # BUILD RESULT
    # =========================================================

    def _build_result(
        self,
        verdict,
        final_class,
        confidence,
        reason,
        ai_metadata_evidence,
        classification_support,
        localization_support,
        evidence_consistent
    ):

        return {

            "verdict":
                verdict,

            "final_class":
                final_class,

            "confidence":
                round(
                    confidence,
                    4
                ),

            "reason":
                reason,

            "evidence": {

                "ai_metadata":
                    ai_metadata_evidence,

                "classifier_support":
                    classification_support,

                "localization_support":
                    localization_support,

                "evidence_consistent":
                    evidence_consistent
            }
        }