import { ArrowRight, Award, BarChart3, CheckCircle2, ChevronRight, ClipboardCheck, Clock3, FileCheck2, FileText, ListTodo, ShieldCheck, Users } from "lucide-react";

type Row = Record<string, any>;
type Page = "Overview" | "Applicants" | "Applications" | "AI Screening" | "Interviews" | "Decisions" | "Settings";
const name = (row: Row): string => String(row.applicant_name || "Unknown applicant");
const title = (value: unknown) => String(value || "Not recorded").replace(/_/g, " ").toLowerCase().replace(/^\w/, c => c.toUpperCase());
// Shared by the donut, its legend and recent-application status labels.
const statusColors: Record<string, string> = {
  DRAFT: "#8BA4CF",
  SUBMITTED: "#115DF4",
  UNDER_REVIEW: "#996500",
  FOR_INTERVIEW: "#7048CB",
  INTERVIEWED: "#3288FF",
  RECOMMENDED: "#008A92",
  APPROVED: "#13835F",
  REJECTED: "#C92E4B",
  WAITLISTED: "#B77912",
  WITHDRAWN: "#8192AE",
};
const statusOrder = Object.keys(statusColors);
const date = (value: unknown) => value ? new Date(String(value)).toLocaleDateString("en-US", { month: "short", day: "2-digit", year: "numeric", timeZone: "Asia/Manila" }) : "Not recorded";

export default function OverviewPage({ data, loading, onOpen }: { data: Row | null; loading: boolean; onOpen: (page: Page) => void }) {
  const stats = data?.stats || {};
  const counts = Object.entries((data?.statusCounts || {}) as Record<string, number>)
    .filter(([, value]) => Number(value) > 0)
    .sort(([left], [right]) => {
      const rank = (status: string) => statusOrder.includes(status) ? statusOrder.indexOf(status) : statusOrder.length;
      return rank(left) - rank(right) || left.localeCompare(right);
    });
  const total = counts.reduce((sum, [, value]) => sum + Number(value), 0);
  let offset = 0;
  const segments = counts.map(([status, value]) => { const start = offset; offset += Number(value) / total * 100; return `${statusColors[status] || "#8BA4CF"} ${start}% ${offset}%`; });
  const cards = [
    { label: "Total applicants", value: stats.applicants, note: "Registered applicant profiles", icon: Users, tone: "blue", page: "Applicants" as Page },
    { label: "Applications", value: stats.applications, note: "Scholarship submissions", icon: FileText, tone: "purple", page: "Applications" as Page },
    { label: "For official review", value: stats.pending, note: "Applications requiring attention", icon: Clock3, tone: "orange", page: "Applications" as Page },
    { label: "Approved scholars", value: stats.approved, note: "Recorded official decisions", icon: Award, tone: "green", page: "Decisions" as Page },
  ];
  const tasks = [
    { label: "Review applications", note: "Submitted and pending records", value: stats.pending, icon: ClipboardCheck, tone: "orange", page: "Applications" as Page },
    { label: "Conduct upcoming interviews", note: "Scheduled and rescheduled interviews", value: stats.interviews, icon: Users, tone: "blue", page: "Interviews" as Page },
    { label: "Record official decisions", note: "Completed interviews awaiting review", value: stats.awaitingDecision, icon: ShieldCheck, tone: "purple", page: "Decisions" as Page },
    { label: "Verify applicant documents", note: "Document validation is not connected", value: null, icon: FileCheck2, tone: "slate", page: "Applicants" as Page },
  ];
  const events: Row[] = data?.recentActivity || [];
  return <div className="reference-overview"><div className="notice overview-advisory"><ShieldCheck size={16} />AI is advisory only. Final decisions are made and recorded by authorized LYDO officials.</div>
    <section className="reference-summary-cards" aria-label="Scholarship summary">{cards.map(card => { const Icon = card.icon; return <button className="reference-summary-card" key={card.label} onClick={() => onOpen(card.page)}><span className={`reference-icon ${card.tone}`}><Icon size={29} /></span><span className="reference-summary-text"><strong>{card.label}</strong><b>{loading ? "…" : card.value ?? "—"}</b><small>{card.note}</small></span><ChevronRight size={16} className="summary-chevron" /></button>; })}</section>
    <section className="reference-overview-middle">
      <section className="reference-panel reference-status-panel"><div className="reference-panel-heading"><BarChart3 size={24} /><div><h2>Application status</h2><p>Official stages &middot; live records</p></div><button onClick={() => onOpen("Applications")}>View all</button></div>
        {total > 0 ? <div className="reference-status-content"><div className="reference-donut" role="img" aria-label={`${total} applications; ${counts.map(([key, count]) => `${title(key)}: ${count}`).join(", ")}`} style={{ background: `conic-gradient(${segments.join(",")})` }}><div><strong>{total}</strong><small>Applications</small></div></div><div className="reference-status-legend">{counts.map(([status, count]) => <div key={status}><i style={{ background: statusColors[status] || "#8BA4CF" }} /><span>{title(status)}</span><b>{count}</b><small>{Math.round(Number(count) / total * 100)}%</small></div>)}</div></div> : <div className="reference-empty">{loading ? "Loading application statuses…" : "No application records yet."}</div>}
      </section>
      <section className="reference-panel reference-recent-panel"><div className="reference-panel-heading"><FileText size={24} /><div><h2>Recent applications</h2><p>Latest scholarship submissions</p></div><button onClick={() => onOpen("Applications")}>View all <ArrowRight size={14} /></button></div><div className="table-scroll"><table className="overview-recent-table"><thead><tr><th>Applicant</th><th>Program</th><th>Official status</th></tr></thead><tbody>{(data?.recentApplications || []).slice(0, 4).map((row: Row) => <tr key={row.application_id}><td><button onClick={() => onOpen("Applications")}>{name(row)}<small>{row.reference_no || `APP-${row.application_id}`}</small></button></td><td>{row.scholarship_program || "Not recorded"}</td><td><span className={`reference-stage stage-${String(row.status || "").toLowerCase()}`} style={{ color: statusColors[String(row.status)] || "#667FA7" }}>{title(row.status)}</span></td></tr>)}</tbody></table></div>{!data?.recentApplications?.length && <div className="reference-empty">{loading ? "Loading recent applications…" : "No recent applications."}</div>}</section>
      <section className="reference-panel reference-tasks-panel"><div className="reference-panel-heading"><ListTodo size={24} /><div><h2>Pending tasks</h2><p>Items that need your attention</p></div><button onClick={() => onOpen("Applications")}>View all <ArrowRight size={14} /></button></div><div className="reference-task-list">{tasks.map(task => { const Icon = task.icon; return <button key={task.label} onClick={() => onOpen(task.page)} disabled={task.value == null}><span className={`reference-task-icon ${task.tone}`}><Icon size={20} /></span><span><strong>{task.label}</strong><small>{task.note}</small></span><b className={task.tone}>{loading ? "…" : task.value ?? "—"}</b></button>; })}</div></section>
    </section>
    <section className="reference-overview-bottom">
      <section className="reference-panel reference-activity-panel"><div className="reference-panel-heading"><Clock3 size={24} /><div><h2>Recent activity</h2><p>Latest recorded scholarship events</p></div><button onClick={() => onOpen("Applications")}>View all</button></div><div className="reference-activity-list">{events.slice(0, 4).map((event, index) => <button key={`${event.type}-${event.id}-${index}`} onClick={() => onOpen(event.type === "interview" ? "Interviews" : event.type === "decision" ? "Decisions" : "Applications")}><time>{date(event.at)}<small>{new Date(String(event.at)).toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit", timeZone: "Asia/Manila" })} PHT</small></time><i style={{ background: ["#526FBA", "#7551FF", "#22B45B", "#00A5B8"][index % 4] }} /><span className={`reference-task-icon ${event.type === "decision" ? "green" : event.type === "interview" ? "purple" : "blue"}`}>{event.type === "decision" ? <CheckCircle2 size={21} /> : event.type === "interview" ? <Users size={21} /> : <FileText size={21} />}</span><span><strong>{event.title}</strong><small>{event.detail}</small></span></button>)}</div>{!events.length && <div className="reference-empty">{loading ? "Loading recorded activity…" : "No recorded activity available."}</div>}</section>
    </section>
  </div>;
}
