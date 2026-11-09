# ForenXNet

## Modular Image Forensics and Tampering Analysis

ForenXNet is a research-oriented image-forensics application that
integrates image-level forgery classification, pixel-level tampering
localization, metadata inspection, experimental source-camera
identification, and evidence fusion in one workflow.

> **Research integrity:** ForenXNet is a decision-support prototype.
> Model outputs are estimates, not proof of authenticity, manipulation,
> or physical camera provenance.

## Contents

1.  Research overview
2.  Problem statement and research gap
3.  Objectives and contributions
4.  Forgery categories
5.  System architecture
6.  Models and modules
7.  Datasets and experimental protocol
8.  Documented results
9.  End-to-end implementation
10. API and frontend
11. Installation and execution
12. Testing
13. Limitations and future work
14. Viva demonstration
15. References
16. Details to verify

------------------------------------------------------------------------

## 1. Research overview

Digital images are used in journalism, social media, insurance, digital
investigations, research, and legal workflows. Image editing tools and
generative models make it easier to alter images or create synthetic
content. Visual inspection alone may not reliably reveal manipulation.

ForenXNet explores a **multi-module forensic workflow**. Rather than
relying on one prediction, it combines:

-   **Forgery classification:** estimates whether an image belongs to
    the real, copy-move, splicing, or AI-generated category.
-   **Tamper localization:** estimates suspicious image regions and
    provides a heatmap, binary mask, and overlay when available.
-   **Metadata inspection:** extracts available camera, capture,
    software, GPS, and file attributes.
-   **Source-camera identification:** experimentally estimates a
    candidate camera class and may reject it as unknown.
-   **Evidence fusion:** combines selected outputs into a consolidated
    assessment.
-   **Reporting interface:** displays evidence, provides analysis
    history, and exports structured JSON.

The central research idea is the integration of complementary evidence
sources into one inspectable workflow, while exposing uncertainty and
limitations.

## 2. Problem statement and research gap

A single image-classification label is often insufficient for forensic
examination. It may indicate a likely category but does not identify
suspicious pixels, explain available metadata, or estimate a possible
source camera. Metadata can be absent or modified, localization can miss
subtle manipulations, and a camera classifier can encounter an unseen
device.

**Problem statement:** Design and implement a modular image-forensics
system that examines digital images using complementary classification,
localization, metadata, and source-camera signals, then presents
available evidence and uncertainty through a unified application.

  -----------------------------------------------------------------------
  Challenge                           ForenXNet design response
  ----------------------------------- -----------------------------------
  Image-level classification does not Pixel-level localization module
  identify suspicious pixels          

  Localization does not provide an    Four-class classification
  overall image category              

  Metadata may be incomplete or       Metadata availability and raw-field
  absent                              display

  Camera candidate may be unknown or  Experimental camera analysis with
  unreliable                          rejection behavior

  Individual signals can disagree     Evidence-fusion stage

  Results can be difficult to inspect Visual evidence, history, and JSON
                                      export
  -----------------------------------------------------------------------

These are design motivations, not claims that every research problem has
been solved. The contribution is system-level integration and
evaluation, not the invention of EfficientNet, U-Net, ResNet, or
metadata extraction.

## 3. Objectives and contributions

### Objectives

1.  Classify images into four forensic categories.
2.  Estimate suspicious regions using segmentation.
3.  Extract and display available metadata.
4.  Investigate source-camera identification with an unknown-camera
    outcome.
5.  Combine available evidence into a consolidated assessment.
6.  Build a frontend and backend for image submission and result
    inspection.
7.  Preserve analysis records and export structured results.

### Contributions

-   Modular forensic workflow connecting complementary components.
-   Four-class EfficientNet-B0 classification experiment.
-   U-Net-based localization component.
-   Metadata extraction and presentation.
-   Experimental source-camera identification with open-set rejection.
-   Evidence-fusion output and React interface for reviewing results.
-   Explicit presentation of missing values, uncertainty, and
    limitations.

## 4. Forgery categories

-   **Real:** an image labelled as real in the dataset and not assigned
    to a manipulation category. A `real` prediction is not a guarantee
    of authenticity.
-   **Copy-move:** a region is copied from one part of an image and
    pasted into another part of the same image.
-   **Splicing:** content from one image is inserted into another image.
    The composite may contain inconsistencies in boundaries, lighting,
    texture, noise, or compression.
-   **AI-generated:** an image created or synthesized using generative
    methods. Its exact definition depends on the dataset labels and
    collection process.

## 5. System architecture

The diagram represents logical components. Confirm actual execution
order and conditional branches in backend orchestration code.

``` text
                         INPUT IMAGE
                              |
                              v
                      React Upload UI
                              |
                              v
                         FastAPI API
                              |
              +---------------+----------------+
              |               |                |
              v               v                v
        EfficientNet-B0      U-Net        Metadata Parser
        Classification    Localization      Extraction
              |               |                |
              +---------------+----------------+
                              |
                              v
                  Source-Camera Identification
                       (Experimental)
                              |
                              v
                       Evidence Fusion
                              |
                              v
                    Structured API Response
                              |
                              v
                       React Results UI
                              |
              +---------------+----------------+
              |               |                |
              v               v                v
         Visual Evidence    History          JSON Export
```

The source-camera component may be conditional. Do not claim every
module runs for every image unless the backend confirms it.

### Technology overview

  -----------------------------------------------------------------------
  Layer                   Technology              Responsibility
  ----------------------- ----------------------- -----------------------
  Frontend                React, Vite, JavaScript Upload, navigation,
                                                  results, history,
                                                  report UI

  Styling                 CSS                     Application layout

  Backend                 FastAPI                 API endpoints and model
                                                  orchestration

  Classification          PyTorch /               Four-class image
                          EfficientNet-B0         classification

  Localization            U-Net implementation    Pixel-level
                                                  localization

  Camera analysis         Experimental classifier Candidate prediction
                                                  and rejection

  Metadata                Metadata extraction     File and image metadata
                          utility                 

  Reporting               JSON                    Structured export
  -----------------------------------------------------------------------

## 6. Models and modules

### 6.1 EfficientNet-B0 --- forgery classification

**Purpose:** Image-level classification into `ai_generated`,
`copy_move`, `real`, and `splicing`. It does not independently produce a
pixel-level tampering mask.

**Why selected:** EfficientNet uses compound scaling, coordinating
network depth, width, and input resolution. B0 is the baseline model and
has approximately 5.3 million parameters in its standard configuration.
It offers a transfer-learning and accuracy/efficiency trade-off. The
project does not claim to have invented EfficientNet.

**Architecture concepts:** - Initial convolution extracts low-level
features. - MBConv (Mobile Inverted Bottleneck Convolution) blocks use
expansion, depthwise convolution, and projection. -
Squeeze-and-Excitation blocks recalibrate feature channels. - Global
pooling aggregates spatial features. - A modified fully connected
classifier maps features to four classes.

**Documented project modification:**

``` python
model = efficientnet_b0(weights="IMAGENET1K_V1")
model.classifier[1] = nn.Linear(
    model.classifier[1].in_features,
    4
)
```

The recorded model output has a 1280-feature input to the final linear
layer and four output classes.

**Documented training configuration**

  Setting                                     Recorded value
  ------------------------- --------------------------------
  Backbone                                   EfficientNet-B0
  Pretraining                     ImageNet (`IMAGENET1K_V1`)
  Input resolution                                 224 × 224
  Classes                                                  4
  Loss                                      CrossEntropyLoss
  Optimizer                                            AdamW
  Learning rate                                       0.0001
  Weight decay                                        0.0001
  Scheduler                                CosineAnnealingLR
  Maximum epochs                                          30
  Batch size                                              32
  Early stopping patience                           5 epochs
  Dropout                                                0.2
  Random seed                                             42
  Mixed precision             Enabled in recorded experiment

**Documented preprocessing**

Training: resize to 256 × 256, random crop to 224 × 224, random
horizontal flip, mild color jitter, and ImageNet normalization.

Validation/testing: resize to 224 × 224 and ImageNet normalization.

Mild augmentation was selected because aggressive transformations can
alter forensic traces.

**Training concepts:** CrossEntropyLoss compares multi-class logits with
the target; AdamW applies adaptive updates and decoupled weight decay;
CosineAnnealingLR changes the learning rate on a cosine schedule; early
stopping monitors validation performance; dropout suppresses activations
during training; mixed precision can reduce memory and improve GPU
throughput.

These values describe the documented experiment. Verify that the
deployed checkpoint was produced by this exact configuration.

### 6.2 U-Net --- tamper localization

**Purpose:** U-Net estimates suspicious regions at pixel level,
complementing image-level classification.

**Architecture:** 1. Encoder progressively extracts features and reduces
spatial resolution. 2. Bottleneck represents deeper contextual
information. 3. Decoder upsamples features to recover spatial
resolution. 4. Skip connections pass higher-resolution encoder features
to corresponding decoder stages, helping preserve spatial details.

The model produces a spatial probability map. A threshold converts it
into a binary mask:

``` python
binary_mask = probability_map >= threshold
```

A higher threshold generally selects fewer pixels; a lower threshold
generally selects more.

**Documented segmentation loss:** Project notes record an earlier setup
using `BCEWithLogitsLoss` combined with Dice loss. BCE measures
pixel-level prediction error; Dice emphasizes overlap with the
ground-truth region.

``` text
Total loss = BCE loss + Dice loss
```

The exact weighting, encoder, image size, optimizer, learning rate,
batch size, and training schedule must be taken from the actual U-Net
configuration. They are not established by frontend code.

**Evaluation:** use ground-truth masks and report Dice, IoU, pixel
precision, pixel recall, and pixel-level F1. A blank mask does not prove
authenticity.

### 6.3 Source-camera identification --- experimental

**Purpose:** Estimate a candidate camera class from learned image
features. This differs from reading a camera model from EXIF metadata.

An earlier API response documented model identifier `resnet50_msp`,
suggesting a ResNet50-based classifier with an MSP-style open-set score.
Verify the current checkpoint and implementation before treating this as
definitive.

**ResNet50:** a deep convolutional network built around residual blocks.
A residual connection adds a block's input to its learned residual
transformation:

``` text
y = F(x) + x
```

Residual connections help train deeper networks. ResNet50 uses
bottleneck blocks with 1×1 and 3×3 convolutions.

**Open-set rejection:** a closed-set classifier assumes every input
belongs to a known class. An open-set system can reject a candidate as
unknown. A standard maximum-softmax-probability score is:

``` text
MSP(x) = maximum softmax score across known classes
```

A threshold may accept a candidate only when its score passes the
configured cutoff. Verify the exact score definition and rejection rule
in the backend.

**Earlier API example:** one previously inspected response reported
`unknown_camera`, candidate class `D01`, candidate label
`Samsung S3Mini`, candidate score approximately 84.95%, acceptance
threshold approximately 98.854%, and no accepted camera. A later UI
screenshot showed 84.08% with `Unknown Camera`. These are separate
examples; do not combine their values as one result.

A candidate score is not automatically a calibrated probability of
physical provenance. Camera traces can be affected by resizing,
recompression, denoising, editing, and splicing. Rejection is imperfect.

**Evaluation:** known-camera accuracy, unknown-device rejection rate,
false acceptance rate, false rejection rate, and AUROC where a suitable
scoring protocol is defined. Exact training hyperparameters and
camera-class mapping must come from the camera training code and
checkpoint.

### 6.4 Metadata extraction

Metadata extraction is a processing component, not necessarily a trained
model. API fields have included:

-   Camera: Make, Model, CameraModelName, LensModel, SerialNumber.
-   Capture: DateTimeOriginal, ExposureTime, FNumber, ISO, FocalLength.
-   Software: Software, CreatorTool, ProcessingSoftware.
-   GPS availability.
-   File information: type, MIME type, dimensions, encoding.
-   Raw extracted metadata and forensic indicators.

Metadata may be missing, removed, modified, or copied. Missing metadata
is not proof of manipulation. Record the actual extraction library,
version, and indicator rules from the backend.

### 6.5 Evidence fusion

Evidence fusion combines outputs from available forensic components into
a consolidated assessment. API responses have included `verdict`,
`final_class`, `confidence`, `reason`, `classifier_support`,
`localization_support`, `evidence_consistent`, and AI metadata evidence.

The exact fusion method must be established from backend code. It may
use rules, thresholds, weighted scores, or another approach. Do not call
it a trained neural network unless it is one.

An `UNCERTAIN` verdict should be interpreted using the reason returned
by the fusion component.

## 7. Datasets and experimental protocol

The research work has referenced:

  Dataset                   Project relevance
  ------------------------- -----------------------------------------
  CASIA                     Image manipulation / forgery research
  CoMoFoD                   Copy-move forgery research
  Dresden Image Database    Camera and real-image research
  VISION                    Camera/source-device research
  AI-GenBench fake subset   AI-generated image examples
  CIFAKE                    Real versus AI-generated image research

Exact versions, licenses, sample counts, class mappings, source URLs,
and split assignments must be taken from experiment scripts and dataset
records. Do not assume every dataset was used to train every module.

A recorded working classification dataset included approximately: -
Real: 1,800 - Copy-move: 1,800 - Splicing: 1,097 - AI-generated: 1,800

A separate AI-GenBench streaming workflow saved 3,000 images for a
Kaggle working directory. Confirm the final training manifest before
reporting definitive dataset sizes.

**Recommended experimental protocol:** 1. Create independent training,
validation, and test partitions. 2. Use stratification where
appropriate. 3. Keep duplicate or related source images in the same
partition to reduce leakage. 4. Apply random augmentation only to
training data. 5. Use validation data for model selection and early
stopping. 6. Evaluate the final model on a held-out test set. 7. Perform
external-dataset evaluation separately.

A previous experiment used `random_split` with subsets sharing an
underlying `ImageFolder` and then changed transforms. This may have
unintentionally changed the training transform. Treat the affected
experiment as preliminary until the split and transforms are corrected
and the model is retrained.

## 8. Documented classification results

The recorded EfficientNet-B0 held-out test results:

  Metric              Result
  ----------------- --------
  Accuracy            88.49%
  Macro precision     88.58%
  Macro recall        88.42%
  Macro F1            88.47%

**Per-class results**

  Class            Precision   Recall     F1
  -------------- ----------- -------- ------
  AI-generated          0.98     0.95   0.96
  Copy-move             0.98     0.97   0.98
  Real                  0.82     0.80   0.81
  Splicing              0.77     0.81   0.79

**Recorded confusion matrix** (rows: actual; columns: predicted):

``` text
                 Predicted
              AI    CM   Real  Splice
AI           723     1     7      30
Copy-move      6   733     4      11
Real           6     7   616     137
Splicing       3     7   126     581
```

The largest confusion was between real and splicing: 137 real images
were predicted as splicing, and 126 splicing images were predicted as
real.

**External evaluation and domain shift:** a preliminary evaluation on 30
unseen Dresden real images produced 5 predictions as real, 15 as
splicing, 6 as copy-move, and 4 as AI. The observed real-class accuracy
in this small evaluation was 5/30 = 16.67%. This indicates substantial
cross-dataset difficulty. It is not a general four-class Dresden
benchmark because the evaluation consisted of 30 real images.

The 88.49% result is an in-domain classification result, not overall
accuracy for the complete ForenXNet pipeline. Localization, camera
identification, and fusion require separate evaluation.

## 9. End-to-end implementation workflow

The intended application flow is:

1.  User opens the React application.
2.  Frontend checks FastAPI availability.
3.  User selects an image.
4.  Frontend validates extension and upload size.
5.  Image is submitted to the backend.
6.  Backend processes the image and executes configured modules.
7.  Classification returns predicted class and class scores.
8.  Localization returns available statistics and visual evidence.
9.  Metadata extraction returns structured and raw metadata.
10. Camera analysis returns a candidate, status, and score information
    when available.
11. Evidence fusion returns its configured assessment.
12. Backend returns a structured response.
13. Frontend displays verdict, class scores, visualizations, metadata,
    and camera output.
14. Saved records can be retrieved through history.
15. User can export the JSON response.

Confirm exact module order and conditional behavior from the backend
orchestration code.

## 10. Backend and API integration

FastAPI is the integration layer between the web application and Python
forensic components.

The supplied frontend imports:

``` javascript
import {
  analyzeImage,
  checkHealth,
  getAnalysis,
  getHistory
} from "./services/api";
```

  Function                    Responsibility
  --------------------------- -----------------------------
  `checkHealth()`             Check backend availability
  `analyzeImage(file)`        Submit image for analysis
  `getHistory()`              Retrieve saved records
  `getAnalysis(analysisId)`   Retrieve one saved analysis

Exact endpoint paths, HTTP methods, request fields, response codes, and
persistence mechanism must be taken from `frontend/src/services/api.js`
and FastAPI route definitions.

### General response shape

``` json
{
  "analysis_id": "...",
  "created_at": "...",
  "filename": "...",
  "image_path": "...",
  "result": {
    "image": {},
    "metadata": {},
    "raw_metadata": {},
    "forgery_classification": {},
    "localization": {},
    "evidence_fusion": {},
    "visualization": {},
    "source_camera": {}
  }
}
```

This is a structural illustration. Individual fields may be null,
absent, or different for another analysis.

## 11. Frontend implementation

The frontend uses React, Vite, JavaScript, and CSS.

### Main screens

1.  **Dashboard:** system status, saved-analysis metrics, recent
    investigations.
2.  **New Analysis:** image selection, drag-and-drop, preview, and
    analysis submission.
3.  **Analysis Results:** fused verdict, classification breakdown,
    visual evidence, metadata, source-camera output, and complete API
    response.
4.  **Analysis History:** saved analyses and navigation to a selected
    record.
5.  **Forensic Report:** JSON export and report-content overview.

### UI behavior

-   The frontend validates file extension and enforces a 25 MB upload
    limit.
-   Null fields should display as unavailable rather than silently
    becoming zero.
-   The source-camera interface separates an accepted camera from a
    closest candidate.
-   Candidate scores must not be presented as confirmed device
    attribution.
-   The API response viewer allows inspection of returned fields.
-   Large base64 images should not be rendered a second time in the
    generic response viewer.

## 12. Installation and execution

Commands below are a starting point. Use the actual project structure
and dependency files.

### Prerequisites

-   Python compatible with backend dependencies.
-   Node.js and npm compatible with frontend dependencies.
-   Model checkpoints and required configuration files.
-   Dataset files for retraining/evaluation. They may not be required
    for inference if trained checkpoints are present.

### Backend setup (Windows PowerShell)

``` powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Start Uvicorn from the directory containing the actual `main.py` module:

``` powershell
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

If the entry point is in a package or another directory, adjust the
import path and working directory. API docs, if enabled:

``` text
http://127.0.0.1:8000/docs
```

### Frontend setup

Open a second terminal:

``` powershell
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite.

### Configuration

Check the API base URL in `frontend/src/services/api.js`. Ensure it
points to the running backend. If frontend and backend use different
origins, configure FastAPI CORS for the actual frontend development
origin.

Do not commit credentials, API keys, or sensitive local paths.

## 13. Testing and validation

### Functional tests

-   Backend health check succeeds.
-   Valid image upload succeeds.
-   Unsupported file extension is rejected.
-   Oversized file is rejected.
-   Analysis response has expected top-level structure.
-   Null fields render without crashing.
-   Visualizations display when returned.
-   History loads saved records.
-   A selected history record opens.
-   JSON export contains the selected response.

### Model tests

**Classification:** accuracy, precision, recall, macro F1, confusion
matrix, per-class metrics, and external-dataset evaluation.

**Localization:** Dice, IoU, pixel precision, and pixel recall against
ground-truth masks.

**Camera identification:** known-camera accuracy, unknown-device
rejection, false acceptance, false rejection, and appropriate open-set
metrics.

**Evidence fusion:** compare fused output with ground truth and with
individual modules; evaluate uncertain and conflicting cases.

### End-to-end tests

Use controlled images with known labels and, where possible, known masks
and camera sources. Save the input, reference, model output, and failure
information to make demonstrations repeatable.

## 14. Limitations and responsible interpretation

1.  A classification result is a model estimate, not proof.
2.  A localization heatmap or mask is model output and must be
    validated.
3.  Metadata can be removed, modified, or copied.
4.  Camera attribution is experimental and does not prove physical
    device provenance.
5.  Open-set rejection is imperfect.
6.  The documented Dresden experiment indicates cross-dataset
    generalization difficulty.
7.  Evidence fusion does not automatically guarantee better decisions.
8.  Dataset construction, duplicates, compression, and split strategy
    affect results.
9.  The prototype is not a certified forensic tool and should not be
    treated as independent legal proof.

## 15. Future work

-   Correct and document independent train/validation/test handling.
-   Repeat experiments with stratified and source-aware splits.
-   Improve cross-dataset generalization.
-   Investigate real/splicing class confusion.
-   Quantitatively validate localization with ground-truth masks.
-   Calibrate camera rejection and evaluate unseen devices.
-   Document and evaluate fusion rules.
-   Improve confidence calibration and uncertainty reporting.
-   Measure inference latency, memory, and hardware requirements.
-   Improve report generation and reproducibility.
-   Evaluate additional datasets and real-world transformations.

## 16. Viva and demonstration guide

Suggested live demonstration:

1.  Open dashboard and show backend connectivity.
2.  Navigate to New Analysis.
3.  Upload a prepared test image.
4.  Run analysis and show actual returned results.
5.  Explain classification scores.
6.  Explain heatmap, binary mask, and overlay.
7.  Inspect metadata and raw metadata.
8.  Explain camera status, candidate score, and threshold if returned.
9.  Explain fusion verdict and reason.
10. Open History and retrieve the record.
11. Export the exact JSON response.

Keep screenshots as backup, but distinguish screenshots from a live
inference run.

**Short project explanation:**

"ForenXNet is a modular image-forensics research system. It combines
four-class forgery classification using EfficientNet-B0, tamper
localization using U-Net, metadata inspection, and experimental
source-camera identification. The outputs are brought together through
an evidence-fusion component and presented through a React frontend
connected to a FastAPI backend. The application supports image upload,
visualization, analysis history, and JSON export. Our research also
examines limitations, particularly cross-dataset generalization and the
uncertainty of camera attribution."

## 17. References

Verify bibliographic details and cite original papers in the final
academic report.

1.  Tan, M. and Le, Q. V., **EfficientNet: Rethinking Model Scaling for
    Convolutional Neural Networks**. Google Research:
    https://research.google/pubs/efficientnet-rethinking-model-scaling-for-convolutional-neural-networks/
2.  Ronneberger, O., Fischer, P. and Brox, T., **U-Net: Convolutional
    Networks for Biomedical Image Segmentation**. MICCAI, 2015.
3.  He, K., Zhang, X., Ren, S. and Sun, J., **Deep Residual Learning for
    Image Recognition**. CVPR, 2016.
4.  Cite the specific source-camera identification, PRNU, and open-set
    device-identification papers used in the literature review.
5.  Cite official dataset papers/documentation for the exact CASIA,
    CoMoFoD, Dresden, VISION, and AI-generated datasets actually used.

## 18. Implementation details to verify before release

-   [ ] Repository URL and project version.
-   [ ] Exact Python and Node.js versions.
-   [ ] Backend and frontend dependency files.
-   [ ] FastAPI entry point and endpoint paths.
-   [ ] Model checkpoint paths and versions.
-   [ ] U-Net encoder, input size, optimizer, learning rate, batch size,
    loss weights, and epochs.
-   [ ] Camera architecture, preprocessing, class mapping, training
    configuration, MSP definition, and rejection threshold.
-   [ ] Metadata extraction library/version and indicator rules.
-   [ ] Evidence-fusion algorithm and decision thresholds.
-   [ ] Dataset versions, licenses, counts, and split manifests.
-   [ ] Whether the reported EfficientNet result matches the deployed
    checkpoint.
-   [ ] Whether the earlier transform-sharing issue was corrected and
    the model retrained.
-   [ ] Quantitative localization and camera-identification results.
-   [ ] End-to-end runtime and hardware used.

------------------------------------------------------------------------

**Research integrity note:** Do not fill unknown implementation values
with assumed defaults. Distinguish what was implemented, what was
experimentally measured, and what remains to be validated. Update this
README whenever checkpoints, API contracts, datasets, or evaluation
protocols change.
