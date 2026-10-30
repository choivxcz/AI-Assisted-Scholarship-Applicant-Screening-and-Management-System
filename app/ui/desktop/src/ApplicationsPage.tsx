import { apiFetch } from "./api";
import { useEffect, useMemo, useRef, useState } from "react";
import { ArrowDownToLine, ArrowUpRight, CalendarPlus, CalendarDays, Check, ChevronDown, ChevronLeft, ChevronRight, ClipboardList, Clock3, Files, Info, LoaderCircle, MoreHorizontal, Pencil, RefreshCw, ScanLine, Search, ShieldCheck, X } from "lucide-react";

type Row = Record<string, any>;
type Props = {
  rows: Row[]; loading: boolean; search: string; setSearch: (value: string) => void;
  refresh: () => void; onScreen: (row: Row) => void; onSchedule: (row: Row) => void;
  onEdit: (row: Row) => void; onStatus: (row: Row) => void; onProfile: (applicantId: number) => void;
};
const reference = (row: Row) => row.reference_no || `APP-${row.application_id}`;
const name = (row: Row): string => String(row.applicant_name || [row.first_name, row.middle_name, row.last_name, row.suffix].filter(Boolean).join(" ") || "Unknown applicant");
const nice = (value: unknown) => value ? String(value).replace(/_/g, " ").toLowerCase().replace(/^\w/, letter => letter.toUpperCase()) : "Not recorded";
const date = (value: unknown) => {
  if (!value) return "Not recorded";
  const parsed = new Date(String(value));
  return Number.isNaN(parsed.getTime()) ? "Not recorded" : parsed.toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric", timeZone: "Asia/Manila" });
};
const tone = (status: unknown) => ({ APPROVED: "approved", REJECTED: "rejected", FOR_INTERVIEW: "interview", UNDER_REVIEW: "review", WAITLISTED: "review" }[String(status)] || "submitted");

export default function ApplicationsPage({ rows, loading, search, setSearch, refresh, onScreen, onSchedule, onEdit, onStatus, onProfile }: Props) {
  const [program, setProgram] = useState("");
  const [year, setYear] = useState("");
  const [stage, setStage] = useState("");
  const [sort, setSort] = useState("updated");
  const [page, setPage] = useState(1);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [closed, setClosed] = useState(false);
  const [tab, setTab] = useState("Overview");
  const [details, setDetails] = useState<{ screening: Row[]; interviews: Row[]; decisions: Row[] }>({ screening: [], interviews: [], decisions: [] });
  const [detailErrors, setDetailErrors] = useState<Record<string, string>>({});
  const [detailLoading, setDetailLoading] = useState(false);
  const searchInput = useRef<HTMLInputElement>(null);
  const options = (key: string) => Array.from(new Set(rows.map(row => row[key]).filter(value => value != null && value !== "").map(String))).sort();
  const matches = useMemo(() => rows.filter(row => `${reference(row)} ${name(row)} ${row.applicant_id}`.toLowerCase().includes(search.toLowerCase()) && (!program || row.scholarship_program === program) && (!year || String(row.scholarship_year) === year) && (!stage || row.status === stage)).sort((a, b) => sort === "name" ? name(a).localeCompare(name(b)) : String(b[sort === "created" ? "created_at" : "updated_at"] || b.created_at || "").localeCompare(String(a[sort === "created" ? "created_at" : "updated_at"] || a.created_at || ""))), [rows, search, program, year, stage, sort]);
  const pages = Math.max(1, Math.ceil(matches.length / 6));
  const current = Math.min(page, pages);
  const visible = matches.slice((current - 1) * 6, current * 6);
  const selected = closed ? undefined : rows.find(row => row.application_id === selectedId) || visible[0];
  const applicationId = selected?.application_id;
  useEffect(() => { setPage(1); }, [search, program, year, stage, sort]);
  useEffect(() => { setTab("Overview"); }, [applicationId]);
  useEffect(() => {
    const focus = (event: KeyboardEvent) => { if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") { event.preventDefault(); searchInput.current?.focus(); } };
    window.addEventListener("keydown", focus);
    return () => window.removeEventListener("keydown", focus);
  }, []);
  useEffect(() => {
    if (!applicationId) return;
    const controller = new AbortController();
    setDetailLoading(true); setDetails({ screening: [], interviews: [], decisions: [] }); setDetailErrors({});
    const sources = [{ key: "screening", path: "screening-results" }, { key: "interviews", path: "interviews" }, { key: "decisions", path: "decisions" }] as const;
    Promise.allSettled(sources.map(async source => {
      const response = await apiFetch(`http://127.0.0.1:8765/api/${source.path}`, { signal: controller.signal });
      if (!response.ok) throw new Error(`${nice(source.key)} records could not be loaded.`);
      const data = await response.json();
      const dateKey = source.key === "screening" ? "screened_at" : source.key === "interviews" ? "scheduled_at" : "decided_at";
      return (data.items || []).filter((row: Row) => Number(row.application_id) === Number(applicationId)).sort((a: Row, b: Row) => String(b[dateKey] || "").localeCompare(String(a[dateKey] || "")));
    })).then(results => {
      if (controller.signal.aborted) return;
      results.forEach((result, index) => {
        const key = sources[index].key;
        if (result.status === "fulfilled") setDetails(previous => ({ ...previous, [key]: result.value }));
        else setDetailErrors(previous => ({ ...previous, [key]: String(result.reason?.message || "Unable to load saved records.") }));
      });
      setDetailLoading(false);
    });
    return () => controller.abort();
  }, [applicationId, rows]);
  const submitted = rows.filter(row => row.status === "SUBMITTED").length;
  const approved = rows.filter(row => row.status === "APPROVED").length;
  const rejected = rows.filter(row => row.status === "REJECTED").length;
  const metrics = [
    { label: "All applications", value: rows.length, note: "Saved scholarship applications", icon: Files, tone: "blue" },
    { label: "Under review", value: rows.filter(row => row.status === "UNDER_REVIEW").length, note: `${submitted} submitted awaiting review`, icon: ClipboardList, tone: "amber" },
    { label: "For interview", value: rows.filter(row => row.status === "FOR_INTERVIEW").length, note: "Manual scheduling available", icon: CalendarDays, tone: "blue" },
    { label: "Final decisions", value: approved + rejected, note: `${approved} approved · ${rejected} rejected`, icon: ShieldCheck, tone: "green" },
  ];
  function select(row: Row) { setSelectedId(row.application_id); setClosed(false); }
  function exportRows() {
    const quote = (value: unknown) => { const text = String(value ?? ""); return `"${(/^[=+@\-\t\r]/.test(text) ? "'" : "") + text.replace(/"/g, '""')}"`; };
    const csv = [["Application ID", "Applicant", "Program", "Scholarship year", "Academic average", "Official status", "Updated"], ...matches.map(row => [reference(row), name(row), row.scholarship_program, row.scholarship_year, row.academic_average, row.status, row.updated_at || row.created_at])].map(row => row.map(quote).join(",")).join("\r\n");
    const url = URL.createObjectURL(new Blob(["\uFEFF", csv], { type: "text/csv;charset=utf-8" }));
    const anchor = document.createElement("a"); anchor.href = url; anchor.download = "applications.csv"; anchor.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  const detailMessage = (key: string, empty: string) => detailLoading ? "Loading saved records…" : detailErrors[key] || empty;
  return <div className="applicants-page applications-page">
    <section className="stats-grid applicants-metrics" aria-label="Application statistics">{metrics.map(metric => { const Icon = metric.icon; return <div className="stat-card" key={metric.label}><span className={`stat-icon ${metric.tone}`}><Icon size={19} /></span><span className="stat-label">{metric.label}</span><div className="stat-value">{loading ? "…" : metric.value}</div><span className="stat-note">{metric.note}</span></div>; })}</section>
    <div className={`applicant-directory-layout ${selected ? "with-profile" : ""}`}>
      <section className="panel applicant-directory"><h2>Application records</h2><p>All programs · Shared scholarship records</p>
        <div className="applicant-search-row"><label className="search-box"><Search size={16} /><input ref={searchInput} aria-label="Search applications" value={search} onChange={event => setSearch(event.target.value)} placeholder="Search applicant or application ID..." /><span>⌘ K</span></label><button className="button-secondary" onClick={exportRows}><ArrowDownToLine size={16} />Export</button></div>
        <div className="applicant-filters"><select aria-label="Program" value={program} onChange={event => setProgram(event.target.value)}><option value="">All programs</option>{options("scholarship_program").map(value => <option key={value}>{value}</option>)}</select><select aria-label="Scholarship year" value={year} onChange={event => setYear(event.target.value)}><option value="">All years</option>{options("scholarship_year").map(value => <option key={value} value={value}>AY {value}</option>)}</select><select aria-label="Official stage" value={stage} onChange={event => setStage(event.target.value)}><option value="">Official stage</option>{options("status").map(value => <option key={value} value={value}>{nice(value)}</option>)}</select><select aria-label="Sort applications" value={sort} onChange={event => setSort(event.target.value)}><option value="updated">Updated date</option><option value="created">Created date</option><option value="name">Applicant A–Z</option></select><button className="button-secondary" aria-label="Refresh applications" onClick={refresh}><RefreshCw size={14} /></button></div>
        <div className="applicant-table-scroll"><table className="applicant-table application-table"><thead><tr><th><span className="record-square" />Application ID <ChevronDown size={9} /></th><th>Applicant</th><th>Program / AY</th><th>Average</th><th>Official status</th><th>Updated</th><th>Actions</th></tr></thead><tbody>{visible.map(row => <tr key={row.application_id} className={applicationId === row.application_id ? "is-selected" : ""}><td><input type="checkbox" aria-label={`View ${reference(row)}`} checked={applicationId === row.application_id} onChange={() => applicationId === row.application_id ? setClosed(true) : select(row)} /><button className="applicant-id" onClick={() => select(row)}>{reference(row)}</button></td><td>{name(row)}</td><td>{row.scholarship_program || "Not recorded"}<small>{row.scholarship_year || "Not recorded"}</small></td><td>{row.academic_average == null ? "—" : Number(row.academic_average).toFixed(2)}</td><td><span className={`application-status ${tone(row.status)}`}>{nice(row.status)}</span></td><td>{date(row.updated_at || row.created_at)}</td><td><button className="applicant-view" onClick={() => select(row)}>View <MoreHorizontal size={13} /></button></td></tr>)}</tbody></table></div>
        {loading && <div className="applicant-empty"><LoaderCircle size={20} className="spin" />Loading applications…</div>}{!loading && !visible.length && <div className="applicant-empty">{search || program || year || stage ? "No applications match your filters." : "No application records in the database yet."}</div>}
        <div className="applicant-pagination"><span>Showing {matches.length ? (current - 1) * 6 + 1 : 0}–{Math.min(current * 6, matches.length)} of {matches.length} records</span><div><button aria-label="Previous page" disabled={current === 1} onClick={() => setPage(current - 1)}><ChevronLeft size={12} /></button>{Array.from({ length: pages }, (_, i) => i + 1).filter(n => n === 1 || n === pages || Math.abs(n - current) <= 1).map(n => <button key={n} className={current === n ? "active" : ""} onClick={() => setPage(n)} aria-label={`Page ${n}`} aria-current={current === n ? "page" : undefined}>{n}</button>)}<button aria-label="Next page" disabled={current === pages} onClick={() => setPage(current + 1)}><ChevronRight size={12} /></button></div></div>
        <div className="applicant-notice"><Info size={16} /><span>Official stages are recorded independently of model predictions. An unfavorable prediction never blocks an authorized action.</span></div>
      </section>
      {selected && <aside className="panel applicant-profile application-profile" aria-label={`${reference(selected)} details`}><div className="applicant-profile-head"><span className="applicant-initials">{name(selected).split(/\s+/).slice(0, 2).map(word => word[0]).join("")}</span><div><h2>{name(selected)}</h2><p>{reference(selected)} · {selected.scholarship_program || "Application"}</p></div><button className="icon-button" aria-label="Close application details" onClick={() => setClosed(true)}><X size={15} /></button></div>
        <div className="applicant-tabs" role="tablist">{["Overview", "AI Screening", "Interview", "Decision/History"].map(value => <button key={value} role="tab" aria-selected={tab === value} className={tab === value ? "active" : ""} onClick={() => setTab(value)}>{value}</button>)}</div>
        <span className={`application-stage-badge application-status ${tone(selected.status)}`}>• {nice(selected.status)}</span>
        {tab === "Overview" && <><dl className="application-overview-fields"><div><dt>Applicant record</dt><dd><button className="application-profile-link" onClick={() => onProfile(Number(selected.applicant_id))}>INB-{selected.applicant_id} · View profile <ArrowUpRight size={12} /></button></dd></div><div><dt>School year</dt><dd>{selected.scholarship_year || "Not recorded"}</dd></div><div><dt>Academic average</dt><dd>{selected.academic_average == null ? "Not recorded" : `${Number(selected.academic_average).toFixed(2)} / 100`}</dd></div><div><dt>School</dt><dd>{selected.school_name || selected.school || "Not recorded"}</dd></div></dl>
          <section className="application-timeline"><h3>Official application timeline</h3><div><span className={selected.submitted_at ? "timeline-mark completed" : "timeline-mark"}>{selected.submitted_at ? <Check size={12} /> : <Clock3 size={12} />}</span><span><strong>{selected.submitted_at ? "Submitted" : "Application created"}</strong><small>{date(selected.submitted_at || selected.created_at)}</small></span></div><div><span className="timeline-mark"><Clock3 size={12} /></span><span><strong>Screening / review</strong><small>{nice(selected.status)} · Current official stage</small></span></div><div><span className="timeline-mark"><Clock3 size={12} /></span><span><strong>Interview</strong><small>{details.interviews.length ? date(details.interviews[0].scheduled_at) : detailMessage("interviews", "No saved interview schedule")}</small></span></div><div><span className={`timeline-mark ${details.decisions.length ? "completed" : ""}`}>{details.decisions.length ? <Check size={12} /> : <Clock3 size={12} />}</span><span><strong>Official decision</strong><small>{details.decisions.length ? `${nice(details.decisions[0].decision)} · ${date(details.decisions[0].decided_at)}` : detailMessage("decisions", "No saved official decision")}</small></span></div></section>
        </>}
        {tab === "AI Screening" && <section className="applicant-detail-section"><h3>Saved advisory results</h3>{details.screening.length ? details.screening.map(row => <dl key={row.screening_id}><div><dt>Outcome</dt><dd>{nice(row.predicted_class)}</dd></div><div><dt>Screened</dt><dd>{date(row.screened_at)}</dd></div></dl>) : <p>{detailMessage("screening", "No saved screening results.")}</p>}</section>}
        {tab === "Interview" && <section className="applicant-detail-section"><h3>Interview records</h3>{details.interviews.length ? details.interviews.map(row => <dl key={row.interview_id}><div><dt>Schedule</dt><dd>{date(row.scheduled_at)}</dd></div><div><dt>Location</dt><dd>{row.location || "Not recorded"}</dd></div><div><dt>Status</dt><dd>{nice(row.status)}</dd></div><div><dt>Result</dt><dd>{nice(row.result)}</dd></div></dl>) : <p>{detailMessage("interviews", "No saved interview schedule.")}</p>}</section>}
        {tab === "Decision/History" && <section className="applicant-detail-section"><h3>Decisions / history</h3>{details.decisions.length ? details.decisions.map(row => <dl key={row.decision_id}><div><dt>Decision</dt><dd>{nice(row.decision)}</dd></div><div><dt>Date</dt><dd>{date(row.decided_at)}</dd></div><div><dt>Reason</dt><dd>{row.reason || "Not recorded"}</dd></div></dl>) : <p>{detailMessage("decisions", "No saved official decision.")}</p>}<dl><div><dt>Created</dt><dd>{date(selected.created_at)}</dd></div><div><dt>Updated</dt><dd>{date(selected.updated_at)}</dd></div></dl></section>}
        <p className="application-advisory">AI screening is an advisory reference, not an official application stage.</p><div className="application-profile-actions"><button className="button-secondary" onClick={() => onScreen(selected)}><ScanLine size={16} />Open screening</button><button className="button-secondary" disabled={selected.status !== "FOR_INTERVIEW"} title={selected.status !== "FOR_INTERVIEW" ? "Application must be at the For Interview stage to schedule." : "Schedule interview"} onClick={() => onSchedule(selected)}><CalendarPlus size={16} />Schedule Interview</button><details className="application-more-actions"><summary>More actions</summary><button className="button-secondary" onClick={() => onEdit(selected)}><Pencil size={14} />Edit application</button><button className="button-secondary" onClick={() => onStatus(selected)}>Update official stage</button></details></div>
      </aside>}
    </div>
  </div>;
}
