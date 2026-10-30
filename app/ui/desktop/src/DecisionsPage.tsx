import { useMemo, useState } from "react";
import { Award, CheckCircle2, Clock3, FileText, Info, RefreshCw, Search, ShieldCheck, X, XCircle } from "lucide-react";

type Row = Record<string, any>;
const label = (value: unknown) => String(value || "Pending review").replace(/_/g, " ").toLowerCase().replace(/^\w/, c => c.toUpperCase());
const date = (value: unknown) => value ? new Date(String(value)).toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric", timeZone: "Asia/Manila" }) : "Not recorded";
const tone = (value: unknown) => value === "APPROVED" ? "approved" : value === "REJECTED" ? "rejected" : "review";
export default function DecisionsPage({ decisions, applications, loading, refresh, onDecision }: { decisions: Row[]; applications: Row[]; loading: boolean; refresh: () => void; onDecision: (row: Row) => void }) {
  const [search, setSearch] = useState("");
  const [decision, setDecision] = useState("");
  const [program, setProgram] = useState("");
  const [page, setPage] = useState(1);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [tab, setTab] = useState("Summary");
  // Keep one visible row per application; retain every returned decision in its audit tab.
  const records = useMemo<Row[]>(() => {
    const latest = new Map<number, Row>();
    [...decisions].sort((a, b) => String(a.decided_at || "").localeCompare(String(b.decided_at || "")) || Number(a.decision_id || 0) - Number(b.decision_id || 0)).forEach(row => latest.set(Number(row.application_id), row));
    const apps = new Map(applications.map(row => [Number(row.application_id), row]));
    latest.forEach((row, key) => { if (!apps.has(key)) apps.set(key, row); });
    return [...apps.values()].map(app => ({ ...app, ...latest.get(Number(app.application_id)), application_id: Number(app.application_id), decision: latest.get(Number(app.application_id))?.decision || null }));
  }, [decisions, applications]);
  const matches = records.filter(row => (!search || `${row.application_id} ${row.applicant_name || ""} ${row.reason || ""} ${row.decided_by || ""}`.toLowerCase().includes(search.toLowerCase())) && (!decision || (decision === "PENDING" ? !row.decision : row.decision === decision)) && (!program || row.scholarship_program === program));
  const pages = Math.max(1, Math.ceil(matches.length / 6));
  const current = Math.min(page, pages);
  const selected = records.find(row => row.application_id === selectedId);
  const metrics = [
    { label: "Pending decision", value: records.filter(row => !row.decision).length, note: "Awaiting an official record", Icon: Clock3, color: "amber" },
    { label: "Approved", value: records.filter(row => row.decision === "APPROVED").length, note: "Officially recorded", Icon: CheckCircle2, color: "green" },
    { label: "Rejected", value: records.filter(row => row.decision === "REJECTED").length, note: "Recorded decision remarks retained", Icon: XCircle, color: "red" },
    { label: "All applications", value: records.length, note: "Shared scholarship records", Icon: FileText, color: "blue" },
  ];
  return <div className="applicants-page decisions-page">
    <div className="applicant-notice decision-authority"><ShieldCheck size={16} />Human authority only. Authorized LYDO officials make final decisions. Model recommendations do not prevent review.</div>
    <section className="stats-grid applicants-metrics">{metrics.map(({ label, value, note, Icon, color }) => <div className="stat-card" key={label}><span className={`stat-icon ${color}`}><Icon size={19} /></span><span className="stat-label">{label}</span><div className="stat-value">{loading ? "…" : value}</div><span className="stat-note">{note}</span></div>)}</section>
    <div className={`applicant-directory-layout ${selected ? "with-profile" : ""}`}><section className="panel applicant-directory"><h2>Decision records</h2><p>Official decisions are recorded by signed-in staff. Processing identity is retained in Activity Log.</p>
      <div className="applicant-search-row"><label className="search-box"><Search size={16} /><input aria-label="Search decision records" placeholder="Search application, applicant or decision maker…" value={search} onChange={e => { setSearch(e.target.value); setPage(1); }} /></label><button className="button-secondary" onClick={refresh} aria-label="Refresh decisions"><RefreshCw size={16} /></button></div>
      <div className="applicant-filters"><select aria-label="Decision" value={decision} onChange={e => { setDecision(e.target.value); setPage(1); }}><option value="">All decisions</option><option value="PENDING">Pending review</option>{[...new Set(decisions.map(row => row.decision).filter(Boolean))].map(value => <option key={value} value={value}>{label(value)}</option>)}</select><select aria-label="Decision program" value={program} onChange={e => { setProgram(e.target.value); setPage(1); }}><option value="">All programs</option>{[...new Set(records.map(row => row.scholarship_program).filter(Boolean))].sort().map(value => <option key={value}>{value}</option>)}</select></div>
      <div className="applicant-table-scroll"><table className="applicant-table decision-table"><thead><tr><th>Application / applicant</th><th>Program</th><th>Official decision</th><th>Maker / date</th><th>Remarks</th><th>Actions</th></tr></thead><tbody>{matches.slice((current - 1) * 6, current * 6).map(row => <tr key={row.application_id} className={selectedId === row.application_id ? "is-selected" : ""}><td><button className="applicant-id" onClick={() => { setSelectedId(row.application_id); setTab("Summary"); }}>{row.reference_no || `APP-${row.application_id}`}</button><small>{row.applicant_name || "Name unavailable"}</small></td><td>{row.scholarship_program || "Not recorded"}</td><td><span className={`application-status ${tone(row.decision)}`}>{label(row.decision)}</span></td><td>{row.decision_maker_name || row.decided_by || "Not recorded"}<small>{row.decision ? date(row.decided_at) : "—"}</small></td><td>{row.reason || row.remarks || (row.decision ? "Not recorded" : "Awaiting official review")}</td><td><button className="applicant-view" onClick={() => { setSelectedId(row.application_id); setTab("Summary"); }}>View ···</button></td></tr>)}</tbody></table></div>
      {(loading || !matches.length) && <div className="applicant-empty">{loading ? "Loading decision records…" : records.length ? "No records match your filters." : "No application or decision records available."}</div>}
      <div className="applicant-pagination"><span>Showing {matches.length ? (current - 1) * 6 + 1 : 0}–{Math.min(current * 6, matches.length)} of {matches.length} records</span><div><button disabled={current === 1} aria-label="Previous page" onClick={() => setPage(current - 1)}>‹</button><button className="active" aria-label={`Page ${current}`}>{current}</button><button disabled={current === pages} aria-label="Next page" onClick={() => setPage(current + 1)}>›</button></div></div>
    </section>{selected && <aside className="panel applicant-profile"><div className="applicant-profile-head"><span className="applicant-initials"><Award size={20} /></span><div><h2>{selected.applicant_name || "Applicant"}</h2><p>APP-{selected.application_id} · Decision summary</p></div><button className="icon-button" aria-label="Close decision summary" onClick={() => setSelectedId(null)}><X size={16} /></button></div><div className="applicant-tabs">{["Summary", "Read-only audit"].map(value => <button key={value} className={tab === value ? "active" : ""} onClick={() => setTab(value)}>{value}</button>)}</div>
      {tab === "Summary" ? <><span className={`application-stage-badge ${tone(selected.decision)}`}>{label(selected.decision)}</span><section className="applicant-detail-section"><dl>{[["Program", selected.scholarship_program], ["Scholarship year", selected.scholarship_year], ["Official stage", label(selected.status)], ["Decision maker", selected.decision_maker_name || selected.decided_by], ["Decision date", selected.decision ? date(selected.decided_at) : "Not recorded"], ["Remarks", selected.reason || selected.remarks], ["Academic average", selected.academic_average]].map(([key, value]) => <div key={key}><dt>{key}</dt><dd>{value ?? "Not recorded"}</dd></div>)}</dl></section><div className="applicant-notice"><Info size={16} />The advisory does not prevent an authorized review or decision.</div></> : <section className="applicant-detail-section"><h3>Returned official records</h3>{decisions.filter(row => Number(row.application_id) === selectedId).map((row, index) => <dl key={row.decision_id || index}><div><dt>Decision</dt><dd>{label(row.decision)}</dd></div><div><dt>Recorded</dt><dd>{date(row.decided_at)}</dd></div><div><dt>Decision maker</dt><dd>{row.decision_maker_name || row.decided_by || "Not recorded"}</dd></div><div><dt>Remarks</dt><dd>{row.reason || row.remarks || "Not recorded"}</dd></div>{row.previous_status && <div><dt>Previous status</dt><dd>{label(row.previous_status)}</dd></div>}</dl>)}{!selected.decision && <p>No official decision recorded.</p>}<p>Additional status history is not connected.</p></section>}
      <button className="button-secondary" onClick={() => onDecision(selected)}>Record decision</button><p>Your verified identity and server timestamp will be recorded in Activity Log.</p>
    </aside>}</div>
  </div>;
}

