import { useEffect, useMemo, useState } from "react";
import { ChevronLeft, ChevronRight, Info, LoaderCircle, RefreshCw, Search, X } from "lucide-react";

type Row = Record<string, any>;
type Props = { items: Row[]; loading: boolean; refresh: () => void };
type ActivityRow = Row & {
  audit_id?: number | string;
  created_at?: string;
  action?: string;
  entity_type?: string;
  entity_id?: number | string | null;
  actor: Row;
  actorName: string;
  actorKey: string;
  description: string;
};
const readable = (value: unknown): string => String(value || "Not recorded").replace(/[_.]+/g, " ").toLowerCase().replace(/\b\w/g, letter => letter.toUpperCase());
const object = (value: unknown): Row => {
  if (typeof value === "string") {
    try { return object(JSON.parse(value)); } catch { return {}; }
  }
  return value && typeof value === "object" && !Array.isArray(value) ? value as Row : {};
};
const scalar = (value: unknown): string => typeof value === "string" || typeof value === "number" || typeof value === "boolean" ? String(value) : "";
const dateKey = (value: unknown) => String(value || "").slice(0, 10);
const dateText = (value: unknown) => {
  if (!value) return "Not recorded";
  const stamp = new Date(String(value));
  return Number.isNaN(stamp.getTime()) ? "Not recorded" : stamp.toLocaleString("en-PH", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit", timeZone: "Asia/Manila" }) + " PHT";
};

// Do not render arbitrary audit JSON: it may contain credentials or personal data.
// Show only workflow metadata, and summarize changed field names rather than values.
function summary(details: Row): string {
  const fields: [string, string][] = [
    ["previous_status", "Previous status"], ["old_status", "Previous status"], ["new_status", "New status"],
    ["status", "Status"], ["result", "Result"], ["decision", "Decision"],
    ["application_id", "Application"], ["applicant_id", "Applicant"], ["interview_id", "Interview"],
  ];
  const parts = fields.filter(([key]) => scalar(details[key]) !== "").map(([key, label]) => `${label}: ${readable(details[key])}`);
  const allowedFields = new Set(["status", "scholarship_program", "scholarship_year", "academic_average", "monthly_income", "household", "children_count", "senior_count", "pwd_count", "dependent", "solo_parent", "four_ps_beneficiary", "spes_beneficiary", "scholars_in_family", "residency", "previous_scholarship", "exam_score", "exam_passed", "first_name", "middle_name", "last_name", "suffix", "birth_date", "sex", "email", "phone", "house_no_street", "barangay", "municipality", "province", "scheduled_at", "location", "remarks", "result", "decision"]);
  const changed = Array.isArray(details.changed_fields) ? details.changed_fields.filter((key: unknown) => typeof key === "string" && allowedFields.has(key)) : Object.keys(object(details.changes)).filter(key => allowedFields.has(key));
  if (changed.length) parts.push(`Updated fields: ${changed.map(readable).join(", ")}`);
  return parts.join(" · ") || "No additional workflow details recorded.";
}

export default function ActivityLogPage({ items, loading, refresh }: Props) {
  const [search, setSearch] = useState("");
  const [user, setUser] = useState("");
  const [action, setAction] = useState("");
  const [entity, setEntity] = useState("");
  const [date, setDate] = useState("");
  const [page, setPage] = useState(1);
  const records = useMemo<ActivityRow[]>(() => items.map((item): ActivityRow => {
    const details = object(item.details);
    const actor = object(details.actor);
    const actorName = scalar(actor.display_name) || scalar(actor.username) || "Not recorded";
    const actorKey = scalar(actor.user_id) || scalar(actor.username) || "__not_recorded";
    return { ...item, actor, actorName, actorKey, description: summary(details) };
  }).sort((left, right) => String(right.created_at || "").localeCompare(String(left.created_at || "")) || Number(right.audit_id || 0) - Number(left.audit_id || 0)), [items]);
  const users = [...new Map(records.map(record => [record.actorKey, record.actorName])).entries()].sort((left, right) => left[1].localeCompare(right[1]));
  const actions = [...new Set(records.map(record => scalar(record.action)).filter(Boolean))].sort();
  const entities = [...new Set(records.map(record => scalar(record.entity_type)).filter(Boolean))].sort();
  const matches = records.filter(record => (!user || record.actorKey === user) && (!action || record.action === action) && (!entity || record.entity_type === entity) && (!date || dateKey(record.created_at) === date) && `${record.actorName} ${scalar(record.actor.username)} ${readable(record.action)} ${readable(record.entity_type)} ${record.entity_id || ""} ${record.description}`.toLowerCase().includes(search.toLowerCase()));
  const pages = Math.max(1, Math.ceil(matches.length / 10));
  const current = Math.min(page, pages);
  const visible = matches.slice((current - 1) * 10, current * 10);
  const filtered = Boolean(search || user || action || entity || date);
  useEffect(() => { setPage(1); }, [search, user, action, entity, date]);

  return <div className="applicants-page activity-log-page">
    <section className="panel applicant-directory">
      <h2>Activity log</h2>
      <p>Monitor who processed scholarship records and when. Times are shown in Asia/Manila.</p>
      <div className="applicant-search-row">
        <label className="search-box"><Search size={16} /><input aria-label="Search activity log" value={search} onChange={event => setSearch(event.target.value)} placeholder="Search staff member, action or record..." /></label>
        <button className="button-secondary" disabled={loading} onClick={refresh}><RefreshCw size={16} />Refresh</button>
      </div>
      <div className="applicant-filters">
        <select aria-label="Filter activity by staff member" value={user} onChange={event => setUser(event.target.value)}><option value="">All staff members</option>{users.map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select>
        <select aria-label="Filter activity by action" value={action} onChange={event => setAction(event.target.value)}><option value="">All actions</option>{actions.map(value => <option key={value} value={value}>{readable(value)}</option>)}</select>
        <select aria-label="Filter activity by record type" value={entity} onChange={event => setEntity(event.target.value)}><option value="">All record types</option>{entities.map(value => <option key={value} value={value}>{readable(value)}</option>)}</select>
        <input type="date" aria-label="Filter activity by date" value={date} onChange={event => setDate(event.target.value)} />
        {filtered && <button className="button-secondary" aria-label="Clear activity filters" onClick={() => { setSearch(""); setUser(""); setAction(""); setEntity(""); setDate(""); }}><X size={14} /></button>}
      </div>
      <div className="applicant-table-scroll"><table className="applicant-table"><thead><tr><th>Date &amp; time</th><th>Processed by</th><th>Role</th><th>Action</th><th>Record</th><th>Details</th></tr></thead><tbody>{visible.map((record, index) => <tr key={record.audit_id ?? index}>
        <td>{dateText(record.created_at)}</td>
        <td><strong>{record.actorName}</strong>{record.actor.username && record.actor.username !== record.actorName && <small>{scalar(record.actor.username)}</small>}</td>
        <td>{record.actor.role ? readable(record.actor.role) : "Not recorded"}</td>
        <td>{readable(record.action)}</td>
        <td>{readable(record.entity_type)}{record.entity_id != null && <small>#{scalar(record.entity_id)}</small>}</td>
        <td>{record.description}</td>
      </tr>)}</tbody></table></div>
      {loading && <div className="applicant-empty"><LoaderCircle className="spin" size={20} />Loading activity records...</div>}
      {!loading && !visible.length && <div className="applicant-empty">{filtered ? "No activity matches your filters." : "No activity has been recorded yet."}</div>}
      <div className="applicant-pagination"><span>Showing {matches.length ? (current - 1) * 10 + 1 : 0}–{Math.min(current * 10, matches.length)} of {matches.length} loaded events</span><div>
        <button aria-label="Previous activity page" disabled={current === 1} onClick={() => setPage(current - 1)}><ChevronLeft size={12} /></button>
        {Array.from({ length: pages }, (_, index) => index + 1).filter(value => value === 1 || value === pages || Math.abs(value - current) <= 1).map(value => <button key={value} aria-label={`Activity page ${value}`} aria-current={current === value ? "page" : undefined} className={current === value ? "active" : ""} onClick={() => setPage(value)}>{value}</button>)}
        <button aria-label="Next activity page" disabled={current === pages} onClick={() => setPage(current + 1)}><ChevronRight size={12} /></button>
      </div></div>
      <div className="applicant-notice"><Info size={16} /><span>Historical events without a recorded staff identity show “Not recorded.” Actor identities are not inferred from applicant names.</span></div>
    </section>
  </div>;
}
