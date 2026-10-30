import { useEffect, useMemo, useRef, useState } from "react";
import { ArrowDownToLine, CalendarPlus, Check, ChevronLeft, ChevronRight, CircleAlert, ClipboardCheck, Clock3, Files, Info, LoaderCircle, MoreHorizontal, RefreshCw, Search, X, BrainCircuit, BarChart3, FileText, FileCheck2, GraduationCap, ShieldCheck, ArrowRight, ExternalLink, ChevronDown, CalendarDays, Users as UsersIcon } from "lucide-react";

type Row = Record<string, any>;
type Props = { latestBatch: { at: string; count: number } | null; applications: Row[]; results: Row[]; failures: Record<string, string>; loading: boolean; search: string; setSearch: (value: string) => void; refresh: () => void; onScreen: (row: Row) => void; onSchedule: (row: Row) => void; onReviewStage: (row: Row) => void; onEndorse: (row: Row) => void };
const label = (value: unknown) => value == null || value === "" ? "Not recorded" : String(value).replace(/_/g, " ").toLowerCase().replace(/^\w/, c => c.toUpperCase());
const reference = (row: Row) => row.reference_no || `APP-${row.application_id}`;
const name = (row: Row): string => String(row.applicant_name || "Unknown applicant");
const explanation = (row?: Row): Row => { try { const value = typeof row?.explanation === "string" ? JSON.parse(row.explanation) : row?.explanation; return value && typeof value === "object" && !Array.isArray(value) ? value : {}; } catch { return {}; } };
const prediction = (row?: Row) => {
  if (!row) return "Not available";
  const value = String(explanation(row).model_prediction ?? "").toLowerCase();
  if (["1", "qualified"].includes(value)) return "Model predicts qualified";
  if (["0", "not qualified", "not_qualified"].includes(value)) return "Model predicts not qualified";
  return row.predicted_class ? `Advisory: ${label(row.predicted_class)}` : "Not available";
};
const date = (value: unknown, withTime = false) => {
  if (!value) return "—";
  const parsed = new Date(String(value));
  if (Number.isNaN(parsed.getTime())) return "—";
  return withTime ? `${parsed.toLocaleTimeString("en-PH", { hour: "2-digit", minute: "2-digit", timeZone: "Asia/Manila" })} PHT` : parsed.toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric", timeZone: "Asia/Manila" });
};
const inputFields = [ ["academic_average", "Academic average"], ["monthly_income", "Monthly income"], ["household", "Household size"], ["children_count", "Children"], ["senior_count", "Seniors"], ["pwd_count", "PWDs"], ["dependent", "Has dependents"], ["solo_parent", "Solo parent"], ["exam_score", "Exam percentage"], ["four_ps_beneficiary", "4Ps beneficiary"], ["spes_beneficiary", "SPES beneficiary"], ["scholars_in_family", "Scholars in family"] ];

export default function ScreeningPage({ applications, results, failures, loading, search, setSearch, refresh, onScreen, onSchedule, onReviewStage, onEndorse }: Props) {
  const [recommendation, setRecommendation] = useState("");
  const [program, setProgram] = useState("");
  const [status, setStatus] = useState("");
  const [dateFilter, setDateFilter] = useState("");
  const [pageSize, setPageSize] = useState(6);
  const [showHelp, setShowHelp] = useState(false);
  const [page, setPage] = useState(1);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [closed, setClosed] = useState(false);
  const [tab, setTab] = useState("Overview");
  const searchInput = useRef<HTMLInputElement>(null);
  const histories = useMemo(() => {
    const grouped = new Map<number, Row[]>();
    [...results].sort((a, b) => String(b.screened_at || "").localeCompare(String(a.screened_at || "")) || Number(b.screening_id) - Number(a.screening_id)).forEach(row => {
      const id = Number(row.application_id); const history = grouped.get(id) || []; history.push(row); grouped.set(id, history);
    });
    return grouped;
  }, [results]);
  const records = useMemo(() => applications.map(application => {
    const history = histories.get(Number(application.application_id)) || [];
    const failure = failures[String(application.application_id)];
    return { application, result: history[0], history, failure, state: failure ? "Run error" : history.length ? "Completed" : "Not yet screened" };
  }), [applications, histories, failures]);
  const matches = records.filter(row => `${reference(row.application)} ${name(row.application)} ${row.application.scholarship_program || ""}`.toLowerCase().includes(search.toLowerCase()) && (!recommendation || prediction(row.result) === recommendation) && (!program || row.application.scholarship_program === program) && (!status || row.state === status) && (!dateFilter || date(row.result?.screened_at) === dateFilter));
  const pages = Math.max(1, Math.ceil(matches.length / pageSize));
  const current = Math.min(page, pages);
  const visible = matches.slice((current - 1) * pageSize, current * pageSize);
  const selected = closed ? undefined : records.find(row => Number(row.application.application_id) === selectedId) || visible[0];
  const currentId = selected?.application.application_id;
  useEffect(() => { setPage(1); }, [search, recommendation, program, status, dateFilter, pageSize]);
  useEffect(() => { setTab("Overview"); }, [currentId]);
  useEffect(() => {
    const focus = (event: KeyboardEvent) => { if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") { event.preventDefault(); searchInput.current?.focus(); } };
    window.addEventListener("keydown", focus); return () => window.removeEventListener("keydown", focus);
  }, []);
  const metrics = [
    { label: "Existing applications", value: records.length, note: "Batch includes every record", icon: FileText, tone: "blue" },
    { label: "Screening complete", value: records.filter(row => row.state === "Completed").length, note: "Latest saved results", icon: Check, tone: "green" },
    { label: "Not yet screened", value: records.filter(row => row.state === "Not yet screened").length, note: "Available for batch screening", icon: Clock3, tone: "orange" },
    { label: "Screening errors", value: records.filter(row => row.failure).length, note: "Errors from this session", icon: CircleAlert, tone: "orange" },
  ];
  function select(id: number) { setSelectedId(Number(id)); setClosed(false); }
  function exportRecords() {
    const quote = (value: unknown) => { const text = String(value ?? ""); return `"${(/^[=+@\-\t\r]/.test(text) ? "'" : "") + text.replace(/"/g, '""')}"`; };
    const csv = [["Application", "Applicant", "Program", "Model recommendation", "Screening status", "Last screened"], ...matches.map(row => [reference(row.application), name(row.application), row.application.scholarship_program, prediction(row.result), row.state, row.result?.screened_at])].map(row => row.map(quote).join(",")).join("\r\n");
    const url = URL.createObjectURL(new Blob(["\uFEFF", csv], { type: "text/csv;charset=utf-8" })); const anchor = document.createElement("a"); anchor.href = url; anchor.download = "screening-records.csv"; anchor.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  const missing = selected ? inputFields.filter(([key]) => selected.application[key] == null || selected.application[key] === "").map(([, title]) => title) : [];
  const saved = explanation(selected?.result);
  return <div className="screening-reference-page">
    <div className="screening-reference-advisory"><Info size={23} /><span><strong>Advisory only:</strong> Model predictions do not award, reject, or exclude anyone from interviews. Official statuses remain unchanged until an authorized human action is recorded.</span></div>
    {showHelp && <div className="screening-reference-help" role="note">Recommendations never change official stages or determine eligibility. Human review remains available. Scheduling follows the existing application workflow and does not depend on the model prediction.</div>}
    <section className="screening-reference-metrics" aria-label="Screening summary">{metrics.map(metric => { const Icon = metric.icon; return <div className="screening-reference-metric" key={metric.label}><span className={`reference-icon ${metric.tone}`}><Icon size={28} /></span><div><h2>{metric.label}</h2><strong>{loading ? "\u2014" : metric.value}</strong><p>{metric.note}</p></div></div>; })}</section>
    <div className={`screening-reference-layout ${selected ? "has-analysis" : ""}`}>
      <section className="screening-reference-records"><div className="screening-reference-toolbar"><div><h2>Screening records</h2><p>Review model recommendations alongside verified records.</p></div></div><div className="screening-search-row"><label className="screening-reference-search"><Search size={17} /><input ref={searchInput} aria-label="Search screening records" value={search} onChange={event => setSearch(event.target.value)} placeholder="Search applicant or application ID..." /><kbd aria-hidden="true">&#8984; K</kbd></label><button className="screening-outline-button" onClick={exportRecords}><ArrowDownToLine size={17} />Export</button><details className="screening-extra-menu"><summary><MoreHorizontal size={16} /><span className="sr-only">More screening options</span></summary><label className="screening-date-filter"><CalendarDays size={16} /><select aria-label="Last screening date" value={dateFilter} onChange={event => setDateFilter(event.target.value)}><option value="">All dates</option>{[...new Set(records.filter(row => row.result?.screened_at).map(row => date(row.result.screened_at)))].map(value => <option key={value}>{value}</option>)}</select></label><p>Model outputs are advisory and do not change official stages. Saved history covers the results returned by the backend.</p>{selected && <div className="screening-maintenance-actions"><button type="button" onClick={() => onScreen(selected.application)}>Run screening for selected application</button><button type="button" onClick={() => onReviewStage(selected.application)}>Change application stage</button></div>}</details></div>
        <div className="screening-reference-filters"><select aria-label="Model recommendation" value={recommendation} onChange={event => setRecommendation(event.target.value)}><option value="">All recommendations</option>{[...new Set(records.map(row => prediction(row.result)))].sort().map(value => <option key={value}>{value}</option>)}</select><select aria-label="Program" value={program} onChange={event => setProgram(event.target.value)}><option value="">All programs</option>{[...new Set(applications.map(row => String(row.scholarship_program || "")).filter(Boolean))].sort().map(value => <option key={value}>{value}</option>)}</select><select aria-label="Screening status" value={status} onChange={event => setStatus(event.target.value)}><option value="">All screening statuses</option>{["Completed", "Not yet screened", "Run error"].map(value => <option key={value}>{value}</option>)}</select><button className="screening-outline-button refresh-screening" aria-label="Refresh screening records" onClick={refresh}><RefreshCw size={18} /></button></div>
        <div className="screening-reference-table-scroll"><table className="screening-reference-table"><colgroup><col style={{ width: "19%" }} /><col style={{ width: "17%" }} /><col style={{ width: "17%" }} /><col style={{ width: "17%" }} /><col style={{ width: "17%" }} /><col style={{ width: "13%" }} /></colgroup><thead><tr><th><span className="screening-empty-checkbox" /> Application <span aria-hidden="true">&darr;</span></th><th>Applicant / program</th><th>Model recommendation</th><th>Screening status</th><th>Last screened</th><th>Actions</th></tr></thead><tbody>{visible.map((row) => <tr key={row.application.application_id} className={currentId === row.application.application_id ? "selected" : ""}><td><div className="screening-application-cell"><input type="checkbox" aria-label={`Review ${reference(row.application)}`} checked={currentId === row.application.application_id} onChange={() => currentId === row.application.application_id ? setClosed(true) : select(row.application.application_id)} /><button className="screening-reference-id" onClick={() => select(row.application.application_id)}>{reference(row.application)}</button></div></td><td><span className="screening-reference-person"><strong>{name(row.application)}</strong></span><small className="screening-program-name">{row.application.scholarship_program || "Not recorded"}</small></td><td><span className={`screening-recommendation ${row.result ? "review" : "unavailable"}`}>{prediction(row.result)}</span></td><td><span className={`screening-reference-state ${row.failure ? "error" : row.result ? "completed" : "pending"}`}>{row.state}</span></td><td><time>{date(row.result?.screened_at)}<small>{row.failure || (row.result ? date(row.result.screened_at, true) : "No saved result")}</small></time></td><td><button className="screening-more-button" aria-label={`Open details for ${reference(row.application)}`} onClick={() => select(row.application.application_id)}>Review <MoreHorizontal size={12} aria-hidden="true" /></button></td></tr>)}</tbody></table></div>
        {loading && <div className="screening-reference-empty"><LoaderCircle size={20} className="spin" />Loading screening records...</div>}{!loading && !visible.length && <div className="screening-reference-empty">{search || recommendation || program || status || dateFilter ? "No records match your filters." : "No application records in the database yet."}</div>}
        <div className="screening-reference-pagination"><span>Showing {matches.length ? (current - 1) * pageSize + 1 : 0}&ndash;{Math.min(current * pageSize, matches.length)} of {matches.length} applications</span><div><label>Rows per page <select aria-label="Screening records per page" value={pageSize} onChange={event => setPageSize(Number(event.target.value))}>{[6, 12, 24].map(value => <option key={value}>{value}</option>)}</select></label><button aria-label="Previous page" disabled={current === 1} onClick={() => setPage(current - 1)}><ChevronLeft size={16} /></button>{Array.from({ length: pages }, (_, i) => i + 1).filter(n => n === 1 || n === pages || Math.abs(n - current) <= 1).map(n => <button key={n} className={current === n ? "active" : ""} aria-current={current === n ? "page" : undefined} aria-label={`Page ${n}`} onClick={() => setPage(n)}>{n}</button>)}<button aria-label="Next page" disabled={current === pages} onClick={() => setPage(current + 1)}><ChevronRight size={16} /></button></div></div>
<p className="screening-record-footnote">Saved model recommendations are advisory. Official application stages remain unchanged.</p>
      </section>
      {selected && <aside className="screening-reference-analysis" aria-label={`${reference(selected.application)} screening analysis`}><header><span className="screening-detail-avatar">{name(selected.application).split(/\s+/).slice(0, 2).map(word => word[0]).join("")}</span><div><h2>{name(selected.application)}</h2><p>{reference(selected.application)} &middot; Screening details</p></div><button aria-label="Close screening details" onClick={() => setClosed(true)}><X size={19} /></button></header>
        <div className="screening-reference-tabs" role="tablist">{["Overview", "Inputs/Analysis", "References", "History"].map(value => <button key={value} role="tab" aria-selected={tab === value} className={tab === value ? "active" : ""} onClick={() => setTab(value)}>{value}</button>)}</div>
        <div className="screening-analysis-content"><div className="screening-detail-status"> <span className={`screening-detail-state ${selected.failure ? "error" : selected.result ? "completed" : "pending"}`}>{selected.state}</span></div>
          {tab === "Overview" && <><section className="screening-advisory-recommendation review"><div><small>ADVISORY MODEL OUTPUT</small><h3>{prediction(selected.result)}</h3><p>Not an official ruling. Human review and authorized interview scheduling remain available.</p></div></section><section className="screening-analysis-tab"><dl><div><dt>Official stage</dt><dd>{label(selected.application.status)} &middot; Unchanged</dd></div><div><dt>Saved input fields</dt><dd>{missing.length ? `${missing.length} fields unavailable` : "Listed inputs present"}</dd></div><div><dt>Model version</dt><dd>{saved.model_version || "Not recorded"}</dd></div><div><dt>Last run</dt><dd>{date(selected.result?.screened_at)} {selected.result ? date(selected.result.screened_at, true) : ""}</dd></div></dl></section><section className="screening-review-notes"><h3>REVIEW NOTES</h3><p>Review eligibility against source records before recording an official action.</p><p>Review-note storage, explainability, and validation metrics are not connected. No uploaded references are connected.</p>{Array.isArray(saved.reasons) && saved.reasons.length > 0 && <p>Saved explanation: {saved.reasons.map((reason: unknown) => typeof reason === "string" ? reason : JSON.stringify(reason)).join(" ")}</p>}</section></>}
          {tab === "Inputs/Analysis" && <section className="screening-analysis-tab"><h3>Saved model analysis</h3><p>{prediction(selected.result)}</p><dl><div><dt>Model version</dt><dd>{saved.model_version || "Not recorded"}</dd></div><div><dt>Last run</dt><dd>{date(selected.result?.screened_at)} {selected.result ? date(selected.result.screened_at, true) : ""}</dd></div><div><dt>Official stage</dt><dd>{label(selected.application.status)}</dd></div></dl><h3>Current saved inputs</h3><dl>{inputFields.map(([key, title]) => <div key={key}><dt>{title}</dt><dd>{selected.application[key] == null || selected.application[key] === "" ? "Not recorded" : String(selected.application[key])}</dd></div>)}</dl>{missing.length > 0 && <p>Missing saved fields: {missing.join(", ")}. The service may substitute defaults.</p>}<p>Current inputs may differ from those used for the saved result. Validation metrics and feature impacts are not available.</p></section>}
          {tab === "References" && <section className="screening-analysis-tab"><h3>Documents</h3><p>No document or source-reference service is connected. Document completeness cannot be scored.</p></section>}
          {tab === "History" && <section className="screening-analysis-tab"><h3>Saved screening history</h3>{selected.history.length ? selected.history.map(result => <dl key={result.screening_id}><div><dt>Screened</dt><dd>{date(result.screened_at)} {date(result.screened_at, true)}</dd></div><div><dt>Recommendation</dt><dd>{prediction(result)}</dd></div><div><dt>Model version</dt><dd>{explanation(result).model_version || "Not recorded"}</dd></div></dl>) : <p>No saved screening history.</p>}</section>}
          {selected.failure && <p className="screening-run-error" role="alert">{selected.failure}</p>}
          <div className="screening-actions-menu"><button className="screening-outline-button screening-review-primary" disabled={!["DRAFT", "SUBMITTED", "UNDER_REVIEW"].includes(String(selected.application.status).toUpperCase())} title="Save the application as For Interview using the existing human endorsement workflow." onClick={() => onEndorse(selected.application)}><ClipboardCheck size={15} />{selected.application.status === "FOR_INTERVIEW" ? "Endorsed for interview" : "Endorse for interview"}</button><button className="screening-outline-button" disabled={selected.application.status !== "FOR_INTERVIEW"} title="The official stage must be For Interview before scheduling." onClick={() => onSchedule(selected.application)}><CalendarPlus size={15} />Schedule Interview</button></div>
        </div>
      </aside>}
    </div>
  </div>;
}
