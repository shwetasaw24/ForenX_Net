

import { useEffect, useRef, useState } from "react";

import {

  Activity, ArrowDownLeft, ArrowLeft, ArrowRight, BarChart3,

  Camera, CheckCircle2, ChevronRight, Clock3, Download,

  FileImage, FileJson, FileText, Fingerprint, FlaskConical,

  FolderClock, Gauge, ImagePlus, LayoutDashboard, LoaderCircle,

  Menu, RefreshCw, ShieldAlert, ShieldCheck, SlidersHorizontal,

  UploadCloud, X, Zap

} from "lucide-react";

import {

  analyzeImage, checkHealth, getAnalysis, getHistory

} from "./services/api";

import "./styles.css";



const NAV = [

  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },

  { id: "analyze", label: "New analysis", icon: ImagePlus },

  { id: "history", label: "Analysis history", icon: FolderClock },

  { id: "report", label: "Forensic report", icon: FileText },

];



const pretty = (value) =>

  String(value ?? "Not available").replaceAll("_", " ");



const percent = (value, digits = 1) =>
  value !== null &&
  value !== undefined &&
  value !== "" &&
  Number.isFinite(Number(value))
    ? `${(Number(value) * 100).toFixed(digits)}%`
    : "—";



function downloadJSON(data, filename = "forenxnet-report.json") {

  const blob = new Blob([JSON.stringify(data, null, 2)], {

    type: "application/json",

  });

  const url = URL.createObjectURL(blob);

  const a = document.createElement("a");

  a.href = url;

  a.download = filename;

  a.click();

  URL.revokeObjectURL(url);

}




function JsonValue({ value }) {
  if (value === null || value === undefined) return <span className="json-null">Not returned (null)</span>;
  if (typeof value === "boolean") return <span>{value ? "Yes (true)" : "No (false)"}</span>;
  if (typeof value === "string" && value.startsWith("data:image/")) {
    return <span className="json-null">Image data URL returned (displayed in Visual Evidence above)</span>;
  }
  if (Array.isArray(value)) {
    if (!value.length) return <span className="json-null">Empty array</span>;
    return <div className="json-array">{value.map((item, index) => <div className="json-array-item" key={index}><span className="json-index">[{index}]</span><JsonValue value={item} /></div>)}</div>;
  }
  if (typeof value === "object") {
    const entries = Object.entries(value);
    if (!entries.length) return <span className="json-null">Empty object</span>;
    return <div className="json-object">{entries.map(([key, child]) => <div className="json-field" key={key}><div className="json-key">{pretty(key)}</div><div className="json-value"><JsonValue value={child} /></div></div>)}</div>;
  }
  return <span>{String(value)}</span>;
}

function ApiResponsePanel({ record }) {
  if (!record) return null;
  return <section className="panel api-response-panel">
    <PanelHeading title="Complete API response" subtitle="Inspect the fields returned by the API. Null and empty values are shown explicitly." />
    <details className="api-response-details"><summary>View all returned fields</summary><div className="api-response-content"><JsonValue value={record} /></div></details>
    <button className="secondary-btn" type="button" onClick={() => downloadJSON(record, `forenxnet-${record.analysis_id || "report"}.json`)}><Download size={16} /> Export exact API response</button>
  </section>;
}

function MetadataGroup({ title, values }) {
  if (!values || typeof values !== "object") return null;
  const entries = Object.entries(values);
  return <div className="metadata-group"><h4>{title}</h4>{entries.length ? entries.map(([key, value]) => <div className="metadata-value-row" key={key}><span>{pretty(key)}</span><strong>{value === null || value === undefined || value === "" ? "Not present" : String(value)}</strong></div>) : <p className="subtle-note">No fields returned.</p>}</div>;
}

function App() {

  const [page, setPage] = useState("dashboard");

  const [health, setHealth] = useState("checking");

  const [history, setHistory] = useState([]);

  const [analysis, setAnalysis] = useState(null);

  const [file, setFile] = useState(null);

  const [preview, setPreview] = useState("");

  const [busy, setBusy] = useState(false);

  const [error, setError] = useState("");

  const [dragging, setDragging] = useState(false);

  const [mobileNav, setMobileNav] = useState(false);

  const fileInput = useRef(null);



  async function refreshHealth() {

    try {

      await checkHealth();

      setHealth("online");

    } catch {

      setHealth("offline");

    }

  }



  async function refreshHistory() {

    try {

      const data = await getHistory();

      setHistory(data.analyses || []);

    } catch {

      setHistory([]);

    }

  }



  useEffect(() => {

    refreshHealth();

    refreshHistory();

  }, []);



  useEffect(() => {

    if (!file) {

      setPreview("");

      return;

    }

    const url = URL.createObjectURL(file);

    setPreview(url);

    return () => URL.revokeObjectURL(url);

  }, [file]);



  function chooseFile(nextFile) {

    setError("");

    if (!nextFile) return;



    const allowed = /\.(jpe?g|png|webp|tiff?|bmp)$/i;

    if (!allowed.test(nextFile.name)) {

      setError("Choose a JPG, PNG, WEBP, TIFF, or BMP image.");

      return;

    }

    if (nextFile.size > 25 * 1024 * 1024) {

      setError("The maximum upload size is 25 MB.");

      return;

    }



    setFile(nextFile);

    setAnalysis(null);

  }



  async function runAnalysis() {

    if (!file || busy) return;

    setBusy(true);

    setError("");

    try {

      const data = await analyzeImage(file);

      setAnalysis(data);

      await refreshHistory();

      setPage("results");

    } catch (err) {

      setError(err.message || "Analysis failed.");

    } finally {

      setBusy(false);

    }

  }



  async function openSaved(record) {

    setError("");

    setBusy(true);

    try {

      const saved = await getAnalysis(record.analysis_id);

      setAnalysis(saved);

      setPage("results");

    } catch (err) {

      setError(err.message || "Could not load this analysis.");

    } finally {

      setBusy(false);

    }

  }



  function newAnalysis() {

    setFile(null);

    setAnalysis(null);

    setError("");

    setPage("analyze");

  }



  const record = analysis;

  const result = record?.result || {};

  const classification = result.forgery_classification || {};

  const localization = result.localization || {};

  const metadata = result.metadata || {};

  const fusion = result.evidence_fusion || {};

  const sci = result.source_camera || {};

  const visualization = result.visualization || {};

  const probabilities = classification.class_probabilities || {};



  const recent = history.slice(0, 5);

  const total = history.length;

  const uncertain = history.filter(

    (item) => item.result?.evidence_fusion?.verdict === "UNCERTAIN"

  ).length;



  return (

    <div className="app-shell">

      <aside className={`sidebar ${mobileNav ? "sidebar-open" : ""}`}>

        <div className="brand">

          <div className="brand-mark"><Fingerprint size={25} /></div>

          <div>

            <div className="brand-name">ForenX<span>Net</span></div>

            <div className="brand-sub">IMAGE INTELLIGENCE</div>

          </div>

          <button className="icon-btn mobile-close" onClick={() => setMobileNav(false)} aria-label="Close menu">

            <X size={19} />

          </button>

        </div>



        <div className="workspace-label">WORKSPACE</div>

        <nav className="nav-list">

          {NAV.map(({ id, label, icon: Icon }) => (

            <button

              key={id}

              className={`nav-item ${page === id || (id === "report" && page === "results") ? "active" : ""}`}

              onClick={() => {

                setPage(id);

                setMobileNav(false);

                setError("");

              }}

            >

              <Icon size={18} />

              <span>{label}</span>

              {id === "history" && total > 0 && <span className="nav-count">{total}</span>}

            </button>

          ))}

        </nav>



        <div className="sidebar-bottom">

          <div className={`system-card ${health}`}>

            <span className="status-dot" />

            <div>

              <strong>Analysis engine</strong>

              <small>{health === "online" ? "API connected" : health === "offline" ? "API unreachable" : "Checking connection…"}</small>

            </div>

            <button className="tiny-btn" onClick={refreshHealth} title="Refresh connection">

              <RefreshCw size={14} />

            </button>

          </div>

          <div className="sidebar-footer">FORENSIC WORKSPACE <span>v1.0</span></div>

        </div>

      </aside>



      {mobileNav && <button className="mobile-backdrop" onClick={() => setMobileNav(false)} aria-label="Close navigation" />}



      <main className="main-area">

        <header className="topbar">

          <div className="topbar-left">

            <button className="icon-btn mobile-menu" onClick={() => setMobileNav(true)} aria-label="Open menu">

              <Menu size={20} />

            </button>

            <div className="breadcrumb">ForenXNet <ChevronRight size={14} /> <span>{page === "results" ? "Analysis results" : NAV.find((n) => n.id === page)?.label || "Forensic report"}</span></div>

          </div>

          <div className="topbar-right">

            <span className={`connection-pill ${health}`}>

              <span className="status-dot" />

              {health === "online" ? "System online" : health === "offline" ? "Disconnected" : "Connecting"}

            </span>

            <button className="primary-btn top-action" onClick={newAnalysis}>

              <ImagePlus size={16} /> New analysis

            </button>

          </div>

        </header>



        {error && (

          <div className="error-banner">

            <ShieldAlert size={18} />

            <span>{error}</span>

            <button onClick={() => setError("")} aria-label="Dismiss error"><X size={16} /></button>

          </div>

        )}



        {page === "dashboard" && (

          <div className="page-content">

            <div className="page-heading">

              <div>

                <div className="eyebrow"><Activity size={14} /> FORENSIC OVERVIEW</div>

                <h1>Image intelligence, <span>with evidence.</span></h1>

                <p>Analyze image integrity, inspect localization evidence, and review forensic indicators.</p>

              </div>

              <button className="primary-btn" onClick={newAnalysis}><UploadCloud size={17} /> Analyze an image</button>

            </div>



            <div className="hero-panel">

              <div className="hero-copy">

                <div className="hero-tag"><Zap size={13} /> FORENSIC ANALYSIS SUITE</div>

                <h2>Investigate the pixels.<br /><span>Understand the evidence.</span></h2>

                <p>Run your image through the connected ForenXNet pipeline for classification, tamper localization, metadata inspection, evidence fusion, and camera analysis.</p>

                <button className="hero-btn" onClick={newAnalysis}>Start new investigation <ArrowRight size={16} /></button>

              </div>

              <div className="hero-art" aria-hidden="true">

                <div className="scan-ring ring-one" />

                <div className="scan-ring ring-two" />

                <div className="scan-core"><Fingerprint size={72} strokeWidth={1.1} /></div>

                <span className="scan-point point-one" />

                <span className="scan-point point-two" />

                <span className="scan-point point-three" />

                <span className="scan-caption">PIXEL ANALYSIS / ACTIVE</span>

              </div>

            </div>



            <div className="section-heading">

              <div><h2>Workspace overview</h2><p>Metrics from analyses saved by your local API.</p></div>

              <button className="text-btn" onClick={refreshHistory}><RefreshCw size={14} /> Refresh</button>

            </div>



            <div className="stat-grid">

              <StatCard icon={FileImage} label="Total analyses" value={total} note="Saved on this machine" />

              <StatCard icon={ShieldAlert} label="Uncertain verdicts" value={uncertain} note="Evidence needs review" />

              <StatCard icon={Gauge} label="Latest classifier" value={recent[0] ? percent(recent[0].result?.forgery_classification?.confidence) : "—"} note={recent[0] ? pretty(recent[0].result?.forgery_classification?.predicted_class) : "No analysis yet"} />

              <StatCard icon={Camera} label="Camera findings" value={recent[0] ? pretty(recent[0].result?.source_camera?.status || "not returned") : "—"} note="Experimental device analysis" />

            </div>



            <div className="section-heading">

              <div><h2>Recent investigations</h2><p>Your latest saved analysis records.</p></div>

              <button className="text-btn" onClick={() => setPage("history")}>View history <ArrowRight size={14} /></button>

            </div>

            <HistoryTable records={recent} onOpen={openSaved} />

            {!history.length && <EmptyState icon={FolderClock} title="No saved analyses yet" text="Upload an image to create your first real analysis record." action="Start an analysis" onAction={newAnalysis} />}

          </div>

        )}



        {page === "analyze" && (

          <div className="page-content narrow-content">

            <PageTitle eyebrow="NEW INVESTIGATION" title="Analyze an image" subtitle="Upload a source image to begin a forensic examination." />

            <div className="workflow-steps">

              <span className="step active"><b>01</b> Upload image</span><span className="step-line" /><span className={`step ${busy ? "active" : ""}`}><b>02</b> Run models</span><span className="step-line" /><span className="step"><b>03</b> Review evidence</span>

            </div>

            <div

              className={`upload-panel ${dragging ? "dragging" : ""} ${preview ? "has-preview" : ""}`}

              onDragOver={(e) => { e.preventDefault(); setDragging(true); }}

              onDragLeave={() => setDragging(false)}

              onDrop={(e) => { e.preventDefault(); setDragging(false); chooseFile(e.dataTransfer.files?.[0]); }}

            >

              {preview ? (

                <div className="preview-layout">

                  <div className="preview-image-wrap"><img src={preview} alt="Selected image preview" /></div>

                  <div className="preview-info">

                    <span className="file-chip"><FileImage size={14} /> READY FOR ANALYSIS</span>

                    <h3>{file.name}</h3>

                    <p>{(file.size / (1024 * 1024)).toFixed(2)} MB · {file.type || "Image file"}</p>

                    <div className="preview-actions">

                      <button className="secondary-btn" onClick={() => fileInput.current?.click()}>Change image</button>

                      <button className="icon-btn danger-icon" onClick={() => setFile(null)} title="Remove image"><X size={17} /></button>

                    </div>

                  </div>

                </div>

              ) : (

                <div className="upload-empty">

                  <div className="upload-icon"><UploadCloud size={30} /></div>

                  <h3>Drop your evidence image here</h3>

                  <p>Or browse your device to select a file</p>

                  <button className="secondary-btn" onClick={() => fileInput.current?.click()}><ImagePlus size={16} /> Browse files</button>

                  <div className="upload-formats">JPG · PNG · WEBP · TIFF · BMP <span>MAX 25 MB</span></div>

                </div>

              )}

              <input ref={fileInput} type="file" hidden accept=".jpg,.jpeg,.png,.webp,.tif,.tiff,.bmp,image/*" onChange={(e) => chooseFile(e.target.files?.[0])} />

            </div>



            <div className="analysis-info-grid">

              <InfoRow icon={BarChart3} title="Forgery classification" text="Scores across real, copy-move, splicing, and AI-generated classes." />

              <InfoRow icon={SlidersHorizontal} title="Tamper localization" text="Pixel-level evidence and visual overlays, when provided by the model." />

              <InfoRow icon={Camera} title="Metadata & camera" text="Inspect available metadata and experimental source-camera predictions." />

            </div>

            <div className="analysis-submit-row">

              <div className="privacy-note"><ShieldCheck size={17} /><span>Images are processed by your local ForenXNet server.</span></div>

              <button className="primary-btn large-btn" disabled={!file || busy || health !== "online"} onClick={runAnalysis}>

                {busy ? <><LoaderCircle className="spin" size={17} /> Analyzing…</> : <><FlaskConical size={17} /> Run forensic analysis <ArrowRight size={16} /></>}

              </button>

            </div>

            {health === "offline" && <p className="field-error">Start the FastAPI server at 127.0.0.1:8000 before analyzing.</p>}

          </div>

        )}



        {page === "results" && (

          <div className="page-content">

            {!record ? (

              <EmptyState icon={FileImage} title="No analysis selected" text="Run a new analysis or select a saved record from history." action="New analysis" onAction={newAnalysis} />

            ) : (

              <>

                <div className="page-heading results-heading">

                  <div>

                    <div className="eyebrow"><CheckCircle2 size={14} /> ANALYSIS COMPLETE</div>

                    <h1>Analysis <span>results</span></h1>

                    <p>{record.filename} · {record.created_at ? new Date(record.created_at).toLocaleString() : "Saved analysis"}</p>

                  </div>

                  <div className="heading-actions">

                    <button className="secondary-btn" onClick={() => downloadJSON(record, `forenxnet-${record.analysis_id}.json`)}><Download size={16} /> Export JSON</button>

                    <button className="primary-btn" onClick={newAnalysis}><ImagePlus size={16} /> New analysis</button>

                  </div>

                </div>



                <div className={`verdict-banner ${String(fusion.verdict || "unknown").toLowerCase()}`}>

                  <div className="verdict-icon"><ShieldAlert size={23} /></div>

                  <div className="verdict-copy"><span>FUSED FORENSIC VERDICT</span><h2>{pretty(fusion.verdict || "Verdict unavailable")}</h2><p>{fusion.reason || "No interpretation was returned by the evidence fusion module."}</p></div>

                  <div className="verdict-class"><small>TOP CLASS</small><strong>{pretty(fusion.final_class || classification.predicted_class || "Unavailable")}</strong><span>{percent(classification.confidence)} score</span></div>

                </div>



                <div className="result-metric-grid">

                  <MetricCard label="Classifier score" value={percent(classification.confidence, 2)} icon={Gauge} accent="blue" />

                  <MetricCard label="Tampered area" value={localization.tampered_area_percentage == null ? "—" : `${Number(localization.tampered_area_percentage).toFixed(2)}%`} icon={Activity} accent="violet" />

                  <MetricCard label="Mean pixel score" value={localization.mean_probability == null ? "—" : percent(localization.mean_probability, 2)} icon={BarChart3} accent="cyan" />

                  <MetricCard label="Metadata fields" value={metadata.metadata_field_count ?? "—"} icon={FileText} accent="amber" />

                </div>



                <div className="results-grid">

                  <section className="panel image-evidence-panel">

                    <PanelHeading title="Visual evidence" subtitle="Images generated or returned by the analysis pipeline." />

                    {visualization.original ? (

                      <div className="evidence-main-image"><img src={visualization.original} alt="Original image from pipeline" /></div>

                    ) : <div className="visual-unavailable">Original image visualization unavailable.</div>}

                    <div className="visual-legend"><span><i className="legend-blue" /> Original</span><span><i className="legend-red" /> Tamper evidence, if detected</span></div>

                    <div className="visual-grid">

                      <VisualTile title="Heatmap" src={visualization.heatmap} />

                      <VisualTile title="Binary mask" src={visualization.binary_mask} />

                      <VisualTile title="Overlay" src={visualization.overlay} />

                    </div>

                    <p className="subtle-note">A blank mask does not prove an image is authentic. Interpret localization alongside classification and other evidence.</p>

                  </section>



                  <section className="panel">

                    <PanelHeading title="Classification breakdown" subtitle="Model scores by predicted class." />

                    <div className="probability-list">

                      {Object.entries(probabilities).sort((a, b) => Number(b[1]) - Number(a[1])).map(([label, value]) => (

                        <div className="probability-item" key={label}>

                          <div className="probability-label"><span>{pretty(label)}</span><strong>{percent(value, 2)}</strong></div>

                          <div className="probability-track"><div className={`probability-fill ${label === classification.predicted_class ? "selected" : ""}`} style={{ width: `${Math.max(0, Math.min(100, Number(value) * 100))}%` }} /></div>

                        </div>

                      ))}

                      {!Object.keys(probabilities).length && <p className="subtle-note">No class probabilities were returned.</p>}

                    </div>

                    <div className="panel-divider" />

                    <div className="detail-row"><span>Localization threshold</span><strong>{localization.threshold ?? "—"}</strong></div>

                    <div className="detail-row"><span>Maximum pixel score</span><strong>{localization.maximum_probability == null ? "—" : percent(localization.maximum_probability, 2)}</strong></div>

                    <div className="detail-row"><span>Classifier support in fusion</span><strong>{fusion.evidence?.classifier_support == null ? "—" : fusion.evidence.classifier_support ? "Yes" : "No"}</strong></div>

                    <div className="detail-row"><span>Localization support in fusion</span><strong>{fusion.evidence?.localization_support == null ? "—" : fusion.evidence.localization_support ? "Yes" : "No"}</strong></div>

                  </section>

                </div>



                <div className="results-grid lower-grid">

                                    <section className="panel">
                    <PanelHeading title="Metadata inspection" subtitle="Metadata extracted from the uploaded file." />
                    <div className="metadata-status"><span className="status-dot" /><strong>{pretty(metadata.metadata_status || "Status unavailable")}</strong></div>
                    <div className="detail-row"><span>Metadata fields found</span><strong>{metadata.metadata_field_count ?? "—"}</strong></div>
                    <div className="detail-row"><span>Metadata completeness</span><strong>{metadata.metadata_completeness == null ? "—" : `${metadata.metadata_completeness}%`}</strong></div>
                    <div className="detail-row"><span>Camera metadata</span><strong>{metadata.camera_metadata_available == null ? "Not returned" : metadata.camera_metadata_available ? "Available" : "Unavailable"}</strong></div>
                    <div className="detail-row"><span>Capture metadata</span><strong>{metadata.capture_metadata_available == null ? "Not returned" : metadata.capture_metadata_available ? "Available" : "Unavailable"}</strong></div>
                    <div className="detail-row"><span>Software metadata</span><strong>{metadata.software_metadata_available == null ? "Not returned" : metadata.software_metadata_available ? "Available" : "Unavailable"}</strong></div>
                    <div className="detail-row"><span>GPS metadata</span><strong>{metadata.gps_metadata_available == null ? "Not returned" : metadata.gps_metadata_available ? "Available" : "Unavailable"}</strong></div>
                    <MetadataGroup title="Camera metadata" values={metadata.camera_metadata} />
                    <MetadataGroup title="Capture metadata" values={metadata.capture_metadata} />
                    <MetadataGroup title="Software metadata" values={metadata.software_metadata} />
                    {Array.isArray(metadata.forensic_indicators) && metadata.forensic_indicators.length > 0 && <div className="indicator-list">{metadata.forensic_indicators.map((item, index) => <span key={`${index}-${item}`}>{pretty(item)}</span>)}</div>}
                    {result.raw_metadata && <details className="raw-metadata-details"><summary>View raw extracted metadata ({Object.keys(result.raw_metadata).length} fields)</summary><div className="metadata-values">{Object.entries(result.raw_metadata).map(([key, value]) => <div key={key}><span>{pretty(key)}</span><strong>{value === null || value === undefined || value === "" ? "Not present" : String(value)}</strong></div>)}</div></details>}
                  </section>



                                    <section className="panel">
                    <PanelHeading title="Source camera identification" subtitle="Experimental device-level analysis." />
                    <div className="sci-symbol"><Fingerprint size={30} /></div>
                    <h3 className="sci-title">{pretty(sci.status || "Status not returned")}</h3>
                    <p className="sci-description">{sci.interpretation_warning || sci.interpretation || sci.message || "No interpretation was returned."}</p>
                    <div className="detail-row"><span>Accepted camera</span><strong>{sci.predicted_camera ?? "Not identified"}</strong></div>
                    <div className="detail-row"><span>Accepted device</span><strong>{sci.predicted_device_name ?? "Not identified"}</strong></div>
                    <div className="detail-row"><span>Closest candidate class</span><strong>{sci.candidate_camera ?? "Not returned"}</strong></div>
                    <div className="detail-row"><span>Closest candidate device</span><strong>{sci.candidate_device_name ?? "Not returned"}</strong></div>
                    <div className="detail-row"><span>Candidate score</span><strong>{percent(sci.confidence, 2)}</strong></div>
                    <div className="detail-row"><span>Open-set score</span><strong>{percent(sci.open_set_score, 2)}</strong></div>
                    <div className="detail-row"><span>Acceptance threshold</span><strong>{percent(sci.threshold, 3)}</strong></div>
                    <div className="detail-row"><span>Unknown camera</span><strong>{sci.is_unknown == null ? "Not returned" : sci.is_unknown ? "Yes" : "No"}</strong></div>
                    <div className="detail-row"><span>SCI module available</span><strong>{sci.available == null ? "Not returned" : sci.available ? "Yes" : "No"}</strong></div>
                    {sci.model && <div className="detail-row"><span>Model</span><strong>{pretty(sci.model)}</strong></div>}
                    {Array.isArray(sci.limitations) && sci.limitations.length > 0 && <div className="indicator-list">{sci.limitations.map((item, index) => <span key={`${index}-${item}`}>{item}</span>)}</div>}
                    {sci.class_probabilities && <details className="raw-metadata-details"><summary>View camera class scores</summary><div className="probability-list">{Object.entries(sci.class_probabilities).sort((a, b) => Number(b[1]) - Number(a[1])).map(([label, value]) => <div className="probability-item" key={label}><div className="probability-label"><span>{pretty(label)}</span><strong>{percent(value, 2)}</strong></div><div className="probability-track"><div className="probability-fill" style={{ width: `${Math.max(0, Math.min(100, Number(value) * 100))}%` }} /></div></div>)}</div></details>}
                    <p className="subtle-note">Candidate devices are not confirmed identifications. Camera predictions do not prove image provenance or authenticity.</p>
                  </section>

                </div>



                <ApiResponsePanel record={record} />

                <div className="report-action-panel">

                  <div className="report-action-icon"><FileJson size={23} /></div>

                  <div><h3>Keep the evidence record</h3><p>Export the saved result as JSON for further review or documentation.</p></div>

                  <button className="secondary-btn" onClick={() => downloadJSON(record, `forenxnet-${record.analysis_id}.json`)}><Download size={16} /> Download report</button>

                </div>

              </>

            )}

          </div>

        )}



        {page === "history" && (

          <div className="page-content">

            <PageTitle eyebrow="CASE ARCHIVE" title="Analysis history" subtitle="Browse real analyses saved by your local ForenXNet API." />

            <div className="history-toolbar">

              <div className="history-total"><FolderClock size={18} /><strong>{total}</strong> saved {total === 1 ? "analysis" : "analyses"}</div>

              <button className="secondary-btn" onClick={refreshHistory}><RefreshCw size={15} /> Refresh history</button>

            </div>

            <HistoryTable records={history} onOpen={openSaved} />

            {!history.length && <EmptyState icon={FolderClock} title="Your archive is empty" text="Completed analyses will appear here after they are saved by the API." action="Analyze an image" onAction={newAnalysis} />}

            {busy && <p className="loading-line"><LoaderCircle size={16} className="spin" /> Loading analysis…</p>}

          </div>

        )}



        {page === "report" && (

          <div className="page-content narrow-content">

            <PageTitle eyebrow="EVIDENCE DOCUMENTATION" title="Forensic report" subtitle="Export the complete JSON response for a saved analysis." />

            {record ? (

              <div className="panel report-detail-panel">

                <div className="report-file-icon"><FileJson size={28} /></div>

                <div className="report-file-copy"><h3>{record.filename}</h3><p>Analysis ID: {record.analysis_id}</p><p>{record.created_at ? new Date(record.created_at).toLocaleString() : "Date unavailable"}</p></div>

                <button className="primary-btn" onClick={() => downloadJSON(record, `forenxnet-${record.analysis_id}.json`)}><Download size={16} /> Export JSON</button>

              </div>

            ) : (

              <EmptyState icon={FileText} title="Choose an analysis first" text="Open a saved analysis from history or run a new analysis to export its report." action="View history" onAction={() => setPage("history")} />

            )}

            <div className="report-note"><ShieldCheck size={20} /><div><strong>Evidence-aware reporting</strong><p>Reports preserve the model output and its uncertainty. A classification score alone is not proof of manipulation, and source-camera results are experimental.</p></div></div>

            <div className="panel report-options">

              <PanelHeading title="Report contents" subtitle="Fields included when the API returns them." />

              {["Analysis identifier and timestamp", "Forgery class scores", "Tamper localization statistics", "Metadata findings and indicators", "Evidence-fusion verdict and reasoning", "Visualization data URLs", "Source-camera result and status"].map((item) => <div className="report-option" key={item}><CheckCircle2 size={16} />{item}</div>)}

              <p className="subtle-note">This version exports JSON. A print-ready PDF report can be added after we verify the report fields and layout.</p>

            </div>

          </div>

        )}



        <footer className="app-footer"><span>FOREN X NET <i>·</i> IMAGE FORENSICS</span><span>Experimental model outputs require human review.</span></footer>

      </main>

    </div>

  );

}



function PageTitle({ eyebrow, title, subtitle }) {

  return <div className="page-title-block"><div className="eyebrow">{eyebrow}</div><h1>{title}</h1><p>{subtitle}</p></div>;

}



function StatCard({ icon: Icon, label, value, note }) {

  return <div className="stat-card"><div className="stat-top"><span>{label}</span><span className="stat-icon"><Icon size={17} /></span></div><div className="stat-value">{value}</div><div className="stat-note">{note}</div></div>;

}



function MetricCard({ icon: Icon, label, value, accent }) {

  return <div className="metric-card"><span className={`metric-icon ${accent}`}><Icon size={18} /></span><div><span>{label}</span><strong>{value}</strong></div></div>;

}



function InfoRow({ icon: Icon, title, text }) {

  return <div className="info-row"><span className="info-icon"><Icon size={18} /></span><div><strong>{title}</strong><p>{text}</p></div></div>;

}



function PanelHeading({ title, subtitle }) {

  return <div className="panel-heading"><div><h3>{title}</h3><p>{subtitle}</p></div></div>;

}



function VisualTile({ title, src }) {

  return <div className="visual-tile"><div className="visual-tile-heading">{title}<span>{src ? "AVAILABLE" : "NOT RETURNED"}</span></div>{src ? <img src={src} alt={title} /> : <div className="visual-placeholder"><FileImage size={22} /><span>Visualization unavailable</span></div>}</div>;

}



function EmptyState({ icon: Icon, title, text, action, onAction }) {

  return <div className="empty-state"><div className="empty-icon"><Icon size={25} /></div><h3>{title}</h3><p>{text}</p>{action && <button className="secondary-btn" onClick={onAction}>{action} <ArrowRight size={15} /></button>}</div>;

}



function HistoryTable({ records, onOpen }) {

  if (!records.length) return null;

  return (

    <div className="panel history-table-panel">

      <div className="history-table-scroll">

        <table className="history-table">

          <thead><tr><th>File / analysis</th><th>Predicted class</th><th>Confidence</th><th>Fusion verdict</th><th>Created</th><th /></tr></thead>

          <tbody>

            {records.map((item) => {

              const result = item.result || {};

              const cls = result.forgery_classification || {};

              const verdict = result.evidence_fusion?.verdict || "Unavailable";

              return <tr key={item.analysis_id}>

                <td><div className="file-cell"><span className="table-file-icon"><FileImage size={17} /></span><div><strong>{item.filename || "Unnamed image"}</strong><small>{item.analysis_id?.slice(0, 12)}…</small></div></div></td>

                <td><span className="class-label">{pretty(cls.predicted_class || "Unavailable")}</span></td>

                <td className="table-confidence">{percent(cls.confidence, 2)}</td>

                <td><span className={`verdict-chip ${String(verdict).toLowerCase()}`}>{pretty(verdict)}</span></td>

                <td className="table-date">{item.created_at ? new Date(item.created_at).toLocaleString() : "—"}</td>

                <td><button className="row-open-btn" onClick={() => onOpen(item)} aria-label="Open analysis"><ArrowRight size={16} /></button></td>

              </tr>;

            })}

          </tbody>

        </table>

      </div>

    </div>

  );

}



export default App;
