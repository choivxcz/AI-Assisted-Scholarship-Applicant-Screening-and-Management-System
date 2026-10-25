
import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import {
  Activity, ArrowRight, Award, BookOpenCheck, CalendarClock, CalendarDays,
  CheckCircle2, CircleHelp, Clock3, FileText, GraduationCap, LayoutDashboard,
  Menu, Plus, RefreshCw, Search, Settings2, ShieldCheck, Sparkles, Users, X,
  BrainCircuit, AlertCircle, LoaderCircle, Pencil, Archive, CalendarPlus,
  ClipboardCheck, UserRoundPlus, ListChecks,
} from "lucide-react";

type Row = Record<string, any>;
type PageKey = "Overview" | "Applicants" | "Applications" | "AI Screening" | "Interviews" | "Decisions";
type Field = {
  key: string;
  label: string;
  type?: "text" | "number" | "date" | "datetime-local" | "email" | "tel" | "select" | "checkbox" | "textarea";
  required?: boolean;
  min?: number;
  max?: number;
  step?: number | string;
  options?: { label: string; value: string }[];
  section?: string;
  placeholder?: string;
  readOnly?: boolean;
};
type FormState = {
  mode: string;
  title: string;
  subtitle: string;
  fields: Field[];
  initial: Row;
  row?: Row;
} | null;

const API = "http://127.0.0.1:8765/api";

const nav: { label: PageKey; icon: typeof LayoutDashboard; group: string }[] = [
  { label: "Overview", icon: LayoutDashboard, group: "WORKSPACE" },
  { label: "Applicants", icon: Users, group: "WORKSPACE" },
  { label: "Applications", icon: FileText, group: "WORKSPACE" },
  { label: "AI Screening", icon: BrainCircuit, group: "WORKSPACE" },
  { label: "Interviews", icon: CalendarDays, group: "MANAGEMENT" },
  { label: "Decisions", icon: Award, group: "MANAGEMENT" },
];

const STATUSES = [
  "DRAFT", "SUBMITTED", "UNDER_REVIEW", "FOR_INTERVIEW", "INTERVIEWED",
  "RECOMMENDED", "APPROVED", "REJECTED", "WAITLISTED", "WITHDRAWN",
];

const nice = (v: unknown) =>
  String(v ?? "—").replace(/_/g, " ").toLowerCase().replace(/\b\w/g, c => c.toUpperCase());

const dateText = (v: unknown) => {
  if (!v) return "—";
  const d = new Date(String(v));
  return Number.isNaN(d.getTime())
    ? String(v)
    : d.toLocaleDateString("en-PH", { month: "short", day: "numeric", year: "numeric" });
};

const nameOf = (r: Row) =>
  r.applicant_name ||
  [r.first_name, r.middle_name, r.last_name, r.suffix].filter(Boolean).join(" ") ||
  "Unnamed applicant";

const statusTone = (v: unknown) => {
  const s = String(v ?? "").toUpperCase();
  if (["APPROVED", "PASSED", "PROCEED_TO_INTERVIEW", "COMPLETED"].includes(s)) return "green";
  if (["REJECTED", "FAILED", "CANCELLED", "WITHDRAWN"].includes(s)) return "red";
  if (["WAITLISTED", "NEEDS_OFFICIAL_REVIEW", "FOR_INTERVIEW", "SCHEDULED", "RESCHEDULED", "UNDER_REVIEW"].includes(s)) return "amber";
  return "blue";
};

const statusOptions = STATUSES.map(s => ({ label: nice(s), value: s }));
const barangayOptions = Array.from({ length: 7 }, (_, i) => ({
  label: `Barangay ${i + 1}`,
  value: `Barangay ${i + 1}`,
}));

// Temporary program choice based on the default used by the older registration form.
// Replace/add options here when the official scholarship-program list is confirmed.
const scholarshipProgramOptions = [
  { label: "LYDO", value: "LYDO" },
];

async function request<T = any>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || `Request failed (${response.status})`);
  return data as T;
}

const post = (path: string, data: Row) =>
  request(path, { method: "POST", body: JSON.stringify(data) });

const put = (path: string, data: Row) =>
  request(path, { method: "PUT", body: JSON.stringify(data) });

const registrationFields: Field[] = [
  { key: "first_name", label: "First Name", required: true, section: "Applicant Details" },
  { key: "middle_name", label: "Middle Name", section: "Applicant Details" },
  { key: "last_name", label: "Last Name", required: true, section: "Applicant Details" },
  { key: "suffix", label: "Suffix", section: "Applicant Details" },
  { key: "birth_date", label: "Birth Date", type: "date", required: true, section: "Applicant Details" },
  {
    key: "sex", label: "Sex", type: "select", required: true,
    options: [
      { label: "Male", value: "MALE" },
      { label: "Female", value: "FEMALE" },
      { label: "Other", value: "OTHER" },
      { label: "Prefer not to say", value: "PREFER_NOT_TO_SAY" },
    ],
    section: "Applicant Details",
  },
  { key: "email", label: "Email", type: "email", required: true, placeholder: "name@example.com", section: "Contact & Address" },
  { key: "phone", label: "Phone Number", type: "tel", required: true, min: 0, placeholder: "09XXXXXXXXX (11 digits)", section: "Contact & Address" },
  { key: "house_no_street", label: "House No. / Street", required: true, section: "Contact & Address" },
  { key: "barangay", label: "Barangay", type: "select", required: true, options: barangayOptions, section: "Contact & Address" },
  { key: "municipality", label: "Municipality", required: true, readOnly: true, section: "Contact & Address" },
  { key: "province", label: "Province", required: true, readOnly: true, section: "Contact & Address" },

  {
    key: "scholarship_program",
    label: "Scholarship Program",
    type: "select",
    required: true,
    options: scholarshipProgramOptions,
    section: "Application Details",
  },
  { key: "scholarship_year", label: "Scholarship Year", type: "number", required: true, min: 2000, max: 2200, section: "Application Details" },
  { key: "academic_average", label: "Academic Average (0–100)", type: "number", required: true, min: 0, max: 100, step: "0.01", placeholder: "Enter 0 to 100", section: "Application Details" },

  { key: "monthly_income", label: "Monthly Household Income (₱)", type: "number", required: true, min: 0, step: "0.01", placeholder: "Enter amount (0 or more)", section: "Household Information" },
  { key: "household", label: "Household Size", type: "number", required: true, min: 1, placeholder: "e.g. 5", section: "Household Information" },
  { key: "children_count", label: "Children Count", type: "number", required: true, min: 0, placeholder: "e.g. 2", section: "Household Information" },
  { key: "senior_count", label: "Senior Count", type: "number", required: true, min: 0, placeholder: "e.g. 1", section: "Household Information" },
  { key: "pwd_count", label: "PWD Count", type: "number", required: true, min: 0, placeholder: "e.g. 0", section: "Household Information" },
  { key: "dependent", label: "Has Dependents", type: "checkbox", required: true, section: "Household Information" },

  { key: "solo_parent", label: "Solo Parent", type: "checkbox", section: "Eligibility" },
  { key: "four_ps_beneficiary", label: "4Ps Beneficiary", type: "checkbox", section: "Eligibility" },
  { key: "spes_beneficiary", label: "SPES Beneficiary", type: "checkbox", section: "Eligibility" },
  { key: "previous_scholarship", label: "Previously Received a Scholarship", type: "checkbox", section: "Eligibility" },
  { key: "scholars_in_family", label: "Other Scholars in Family", type: "number", required: true, min: 0, placeholder: "e.g. 1", section: "Eligibility" },
  { key: "residency", label: "Residency / Years in Municipality", required: true, placeholder: "Enter years of residency", section: "Eligibility" },

  { key: "exam_total_items", label: "Entrance Exam Total Items", type: "number", required: true, min: 1, placeholder: "e.g. 40", section: "Examination" },
  { key: "exam_raw_score", label: "Entrance Exam Raw Score", type: "number", required: true, min: 0, placeholder: "Must not exceed total items", section: "Examination" },
];

const applicantEditFields: Field[] = [
  { key: "first_name", label: "First name", required: true },
  { key: "middle_name", label: "Middle name" },
  { key: "last_name", label: "Last name", required: true },
  { key: "suffix", label: "Suffix" },
  { key: "birth_date", label: "Birth date", type: "date", required: true },
  {
    key: "sex", label: "Sex", type: "select", required: true,
    options: [
      { label: "Male", value: "MALE" },
      { label: "Female", value: "FEMALE" },
      { label: "Other", value: "OTHER" },
      { label: "Prefer not to say", value: "PREFER_NOT_TO_SAY" },
    ],
  },
  { key: "email", label: "Email", type: "email", required: true },
  { key: "phone", label: "Phone number", type: "tel", required: true },
  { key: "house_no_street", label: "House no. / street", required: true },
  { key: "barangay", label: "Barangay", required: true },
  { key: "municipality", label: "Municipality", required: true },
  { key: "province", label: "Province", required: true },
];

const applicationEditFields: Field[] = [
  {
    key: "scholarship_program", label: "Scholarship Program", type: "select", required: true,
    options: scholarshipProgramOptions,
  },
  { key: "scholarship_year", label: "Scholarship year", type: "number", required: true, min: 2000, max: 2200 },
  { key: "academic_average", label: "Academic average", type: "number", required: true, min: 0, max: 100, step: "0.01" },
  { key: "monthly_income", label: "Monthly household income (₱)", type: "number", required: true, min: 0, step: "0.01" },
  { key: "household", label: "Household size", type: "number", required: true, min: 1 },
  { key: "children_count", label: "Children count", type: "number", required: true, min: 0 },
  { key: "senior_count", label: "Senior count", type: "number", required: true, min: 0 },
  { key: "pwd_count", label: "PWD count", type: "number", required: true, min: 0 },
  { key: "dependent", label: "Has dependents", type: "checkbox", required: true },
  { key: "solo_parent", label: "Solo parent", type: "checkbox", required: true },
  { key: "four_ps_beneficiary", label: "4Ps beneficiary", type: "checkbox", required: true },
  { key: "spes_beneficiary", label: "SPES beneficiary", type: "checkbox", required: true },
  { key: "previous_scholarship", label: "Previous scholarship", type: "checkbox", required: true },
  { key: "scholars_in_family", label: "Other scholars in family", type: "number", required: true, min: 0 },
  { key: "residency", label: "Residency", required: true },
  { key: "exam_raw_score", label: "Exam raw score", type: "number", required: true, min: 0 },
  { key: "exam_total_items", label: "Exam total items", type: "number", required: true, min: 1 },
];

export default function App() {
  const [page, setPage] = useState<PageKey>("Overview");
  const [mobileNav, setMobileNav] = useState(false);
  const [search, setSearch] = useState("");
  const [refreshKey, setRefreshKey] = useState(0);
  const [dashboard, setDashboard] = useState<Row | null>(null);
  const [rows, setRows] = useState<Row[]>([]);
  const [applicationOptions, setApplicationOptions] = useState<{ label: string; value: string }[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [bridgeOnline, setBridgeOnline] = useState(false);
  const [form, setForm] = useState<FormState>(null);
  const [formBusy, setFormBusy] = useState(false);
  const [toast, setToast] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      let health: { ok: boolean } | null = null;
      let healthError: unknown = null;

      for (let attempt = 0; attempt < 15; attempt++) {
        try {
          health = await request<{ ok: boolean }>("/health");
          break;
        } catch (e) {
          healthError = e;
          await new Promise(resolve => window.setTimeout(resolve, 300));
        }
      }

      if (!health) {
        throw healthError instanceof Error
          ? healthError
          : new Error("Python bridge did not start.");
      }

      setBridgeOnline(health.ok);

      if (page === "Overview") {
        const d = await request<Row>("/dashboard");
        setDashboard(d);
        setRows(d.recentApplications || []);
      } else {
        const endpoint: Record<PageKey, string> = {
          Overview: "/dashboard",
          Applicants: "/applicants",
          Applications: "/applications",
          "AI Screening": "/screening-results",
          Interviews: "/interviews",
          Decisions: "/decisions",
        };

        const result = await request<any>(endpoint[page]);
        setRows(
          page === "Interviews"
            ? [
                ...(result.items || []),
                ...(result.awaitingSchedule || []).map((x: Row) => ({
                  ...x,
                  status: "AWAITING SCHEDULE",
                  awaiting_schedule: true,
                })),
              ]
            : result.items || [],
        );
      }

      const apps = await request<{ items: Row[] }>("/applications");
      setApplicationOptions(
        (apps.items || []).map(a => ({
          label: `${a.application_id} · ${nameOf(a)} — ${a.scholarship_program || "Scholarship"}`,
          value: String(a.application_id),
        })),
      );
    } catch (e) {
      setBridgeOnline(false);
      setError(e instanceof Error ? e.message : "Unable to connect to the Python backend.");
    } finally {
      setLoading(false);
    }
  }, [page, refreshKey]);

  useEffect(() => { void load(); }, [load]);
  useEffect(() => {
    if (!toast) return;
    const id = window.setTimeout(() => setToast(""), 4500);
    return () => window.clearTimeout(id);
  }, [toast]);

  const filtered = useMemo(
    () => rows.filter(row => JSON.stringify(row).toLowerCase().includes(search.toLowerCase())),
    [rows, search],
  );

  const refresh = () => setRefreshKey(n => n + 1);
  const showError = (e: unknown) => setToast(e instanceof Error ? e.message : "The operation could not be completed.");

  function openRegistration() {
    const initial: Row = {
      municipality: "Santa Cruz",
      province: "Laguna",
      sex: "PREFER_NOT_TO_SAY",
      scholarship_program: "LYDO",
      scholarship_year: new Date().getFullYear(),
      household: "",
      children_count: "",
      senior_count: "",
      pwd_count: "",
      dependent: false,
      solo_parent: false,
      four_ps_beneficiary: false,
      spes_beneficiary: false,
      previous_scholarship: false,
      scholars_in_family: "",
      exam_raw_score: "",
      exam_total_items: "",
    };

    setForm({
      mode: "register",
      title: "Register applicant & application",
      subtitle: "Applicant details and scholarship information are saved together using your existing registration service.",
      fields: registrationFields,
      initial,
    });
  }

  function openApplicantEdit(row: Row) {
    setForm({
      mode: "editApplicant",
      title: "Edit applicant profile",
      subtitle: `Update contact and personal information for ${nameOf(row)}.`,
      fields: applicantEditFields,
      initial: { ...row },
      row,
    });
  }

  function openApplicationEdit(row: Row) {
    setForm({
      mode: "editApplication",
      title: "Edit application",
      subtitle: `Update application and eligibility inputs for application #${row.application_id}.`,
      fields: applicationEditFields,
      initial: { ...row },
      row,
    });
  }

  function openStatus(row: Row) {
    setForm({
      mode: "status",
      title: "Change application status",
      subtitle: "The existing ApplicationService validates allowed status transitions.",
      fields: [{ key: "status", label: "New status", type: "select", required: true, options: statusOptions }],
      initial: { status: row.status },
      row,
    });
  }

  function openScreening(row?: Row) {
    setForm({
      mode: "screen",
      title: "Run AI-assisted screening",
      subtitle: "Runs the existing saved Random Forest model and persists the advisory result. It never makes the final scholarship decision.",
      fields: [{ key: "application_id", label: "Application", type: "select", required: true, options: applicationOptions }],
      initial: { application_id: row?.application_id ? String(row.application_id) : "" },
      row,
    });
  }

  function openSchedule(row: Row) {
    setForm({
      mode: "schedule",
      title: "Schedule an interview",
      subtitle: `Schedule an interview for ${nameOf(row)}. Only FOR_INTERVIEW applications can be scheduled.`,
      fields: [
        { key: "scheduled_at", label: "Date & time", type: "datetime-local", required: true },
        { key: "location", label: "Location / venue" },
        { key: "remarks", label: "Notes", type: "textarea" },
      ],
      initial: {},
      row,
    });
  }

  function openInterviewResult(row: Row) {
    setForm({
      mode: "interviewResult",
      title: "Record interview result",
      subtitle: `Complete interview #${row.interview_id} and save the official interview result.`,
      fields: [
        {
          key: "result", label: "Interview result", type: "select", required: true,
          options: [
            { label: "Passed", value: "PASSED" },
            { label: "Failed", value: "FAILED" },
            { label: "For further review", value: "FOR_FURTHER_REVIEW" },
          ],
        },
        { key: "remarks", label: "Official remarks", type: "textarea", required: true },
      ],
      initial: { result: "FOR_FURTHER_REVIEW", remarks: row.remarks || "" },
      row,
    });
  }

  function openDecision(row?: Row) {
    setForm({
      mode: "decision",
      title: "Record scholarship decision",
      subtitle: "This saves the decision and updates the linked application status using your existing repository.",
      fields: [
        { key: "application_id", label: "Application", type: "select", required: true, options: applicationOptions },
        {
          key: "decision", label: "Decision", type: "select", required: true,
          options: [
            { label: "Approved", value: "APPROVED" },
            { label: "Rejected", value: "REJECTED" },
            { label: "Waitlisted", value: "WAITLISTED" },
          ],
        },
        { key: "reason", label: "Reason / justification", type: "textarea", required: true },
      ],
      initial: { application_id: row?.application_id ? String(row.application_id) : "", decision: "APPROVED", reason: "" },
      row,
    });
  }

  async function submitForm(values: Row) {
    if (!form) return;
    setFormBusy(true);

    try {
      if (form.mode === "register") {
        const applicantKeys = [
          "first_name", "middle_name", "last_name", "suffix", "birth_date", "sex",
          "email", "phone", "house_no_street", "barangay", "municipality", "province",
        ];

        const applicant: Row = {};
        applicantKeys.forEach(k => { applicant[k] = values[k] ?? ""; });

        const application: Row = {};
        [
          "scholarship_program", "scholarship_year", "academic_average", "monthly_income",
          "household", "children_count", "senior_count", "pwd_count", "dependent",
          "solo_parent", "four_ps_beneficiary", "spes_beneficiary", "previous_scholarship",
          "scholars_in_family", "residency", "exam_raw_score", "exam_total_items",
        ].forEach(k => { application[k] = values[k] ?? null; });

        application.status = "DRAFT";
        application.submitted_at = null;

        const result = await post("/register", { applicant, application });
        setToast(`Registered applicant #${result.applicant_id} and application #${result.application_id}.`);
      } else if (form.mode === "editApplicant") {
        await put(`/applicants/${form.row?.applicant_id}`, values);
        setToast("Applicant profile updated.");
      } else if (form.mode === "editApplication") {
        const payload: Row = { ...values };
        ["scholarship_year", "household", "children_count", "senior_count", "pwd_count", "scholars_in_family", "exam_raw_score", "exam_total_items"]
          .forEach(k => {
            if (payload[k] !== undefined && payload[k] !== null && payload[k] !== "") payload[k] = Number(payload[k]);
          });
        if (payload.academic_average !== undefined) payload.academic_average = Number(payload.academic_average);
        if (payload.monthly_income !== undefined) payload.monthly_income = Number(payload.monthly_income);

        await put(`/applications/${form.row?.application_id}`, payload);
        setToast("Application updated.");
      } else if (form.mode === "status") {
        await put(`/applications/${form.row?.application_id}`, { status: values.status });
        setToast("Application status updated.");
      } else if (form.mode === "screen") {
        const result = await post("/screening", { application_id: Number(values.application_id) });
        setToast(`Screening saved for application #${values.application_id}. ${result.result?.predicted_class || "Review the result in AI Screening."}`);
        setPage("AI Screening");
      } else if (form.mode === "schedule") {
        await post("/interviews", {
          application_id: Number(form.row?.application_id),
          scheduled_at: values.scheduled_at,
          location: values.location || null,
          remarks: values.remarks || null,
        });
        setToast("Interview scheduled.");
      } else if (form.mode === "interviewResult") {
        await post(`/interviews/${form.row?.interview_id}/result`, { result: values.result, remarks: values.remarks });
        setToast("Interview result saved.");
      } else if (form.mode === "decision") {
        await post("/decisions", {
          application_id: Number(values.application_id),
          decision: values.decision,
          reason: values.reason,
        });
        setToast("Scholarship decision saved.");
      }

      setForm(null);
      refresh();
    } catch (e) {
      showError(e);
    } finally {
      setFormBusy(false);
    }
  }

  async function archiveApplicant(row: Row) {
    if (!window.confirm(`Archive ${nameOf(row)}? This uses the existing archive operation and removes the applicant from active lists.`)) return;

    try {
      await request(`/applicants/${row.applicant_id}`, { method: "DELETE" });
      setToast("Applicant archived.");
      refresh();
    } catch (e) {
      showError(e);
    }
  }

  return (
    <div className="app-shell">
      <aside className={`sidebar ${mobileNav ? "sidebar-open" : ""}`}>
        <div className="brand">
          <div className="brand-mark"><GraduationCap size={23} /></div>
          <div>
            <div className="brand-name">iskolar<span>.</span></div>
            <div className="brand-sub">NG BAYAN · ADMIN</div>
          </div>
          <button className="icon-button mobile-close" onClick={() => setMobileNav(false)} aria-label="Close menu"><X size={18} /></button>
        </div>
        <div className="sidebar-divider" />
        {(["WORKSPACE", "MANAGEMENT"] as const).map(group => (
          <div className="nav-group" key={group}>
            <div className="nav-caption">{group}</div>
            {nav.filter(n => n.group === group).map(item => {
              const Icon = item.icon;
              return (
                <button
                  key={item.label}
                  className={`nav-item ${page === item.label ? "active" : ""}`}
                  onClick={() => { setPage(item.label); setSearch(""); setMobileNav(false); }}
                >
                  <Icon size={18} />
                  <span>{item.label}</span>
                  {item.label === "AI Screening" && <span className="nav-new">AI</span>}
                </button>
              );
            })}
          </div>
        ))}
        <div className="sidebar-spacer" />
        <div className="sidebar-assist">
          <div className="assist-icon"><Sparkles size={17} /></div>
          <div className="assist-title">Scholarship insights</div>
          <p>Review applicant progress and screening outcomes in one place.</p>
          <button onClick={() => setPage("AI Screening")}>Explore screening <ArrowRight size={14} /></button>
        </div>
        <div className="sidebar-bottom">
          <div className="avatar">IB</div>
          <div className="profile-copy"><strong>Scholarship Admin</strong><span>Local workspace</span></div>
          <button className="icon-button" title="Settings are managed by your application"><Settings2 size={17} /></button>
        </div>
      </aside>

      {mobileNav && <button className="nav-scrim" onClick={() => setMobileNav(false)} aria-label="Close navigation" />}

      <main className="main-area">
        <header className="topbar">
          <div className="topbar-left">
            <button className="icon-button mobile-menu" onClick={() => setMobileNav(true)} aria-label="Open menu"><Menu size={20} /></button>
            <div className="breadcrumb">Workspace <span>/</span> <strong>{page}</strong></div>
          </div>
          <div className="topbar-actions">
            <div className={`connection-pill ${bridgeOnline ? "online" : "offline"}`}>
              <span className="connection-dot" />{bridgeOnline ? "Backend connected" : "Backend offline"}
            </div>
            <button className="icon-button" title="Refresh data" onClick={refresh}><RefreshCw size={17} /></button>
            <button className="icon-button" title="Help"><CircleHelp size={18} /></button>
            <div className="topbar-avatar">SA</div>
          </div>
        </header>

        <div className="page-content">
          <div className="page-heading">
            <div>
              <div className="eyebrow">SCHOLARSHIP MANAGEMENT</div>
              <h1>{page === "Overview" ? "Good day, Admin" : page}</h1>
              <p>{page === "Overview" ? "Live records from your local scholarship database." : pageDescription(page)}</p>
            </div>
            <div className="heading-actions">
              <div className="date-chip"><CalendarClock size={16} />{new Date().toLocaleDateString("en-PH", { month: "short", day: "numeric", year: "numeric" })}</div>
              {page === "Applicants" && <button className="primary-button" onClick={openRegistration}><UserRoundPlus size={17} /> Register applicant</button>}
              {page === "Applications" && <button className="primary-button" onClick={openRegistration}><Plus size={17} /> New application</button>}
              {page === "AI Screening" && <button className="primary-button" onClick={() => openScreening()}><BrainCircuit size={17} /> Run screening</button>}
              {page === "Decisions" && <button className="primary-button" onClick={() => openDecision()}><Plus size={17} /> Record decision</button>}
            </div>
          </div>

          {error && (
            <div className="error-banner">
              <AlertCircle size={18} />
              <div>
                <strong>Could not load live data</strong>
                <span>{error}</span>
                <small>Check that MySQL is running and your project .env file is configured, then retry.</small>
              </div>
              <button className="button-secondary" onClick={refresh}>Retry</button>
            </div>
          )}

          {page === "Overview"
            ? <Dashboard data={dashboard} rows={rows} loading={loading} onOpen={setPage} />
            : <DataPage
                page={page}
                rows={filtered}
                loading={loading}
                search={search}
                setSearch={setSearch}
                refresh={refresh}
                onRegister={openRegistration}
                onApplicantEdit={openApplicantEdit}
                onApplicantArchive={archiveApplicant}
                onApplicationEdit={openApplicationEdit}
                onStatus={openStatus}
                onScreen={openScreening}
                onSchedule={openSchedule}
                onInterviewResult={openInterviewResult}
                onDecision={openDecision}
              />}

          <footer className="footer">
            <span>© {new Date().getFullYear()} Iskolar ng Bayan</span>
            <span><span className="footer-dot" /> Local desktop workspace <span className="footer-sep">·</span> Scholarship Applicant Screening & Management</span>
          </footer>
        </div>
      </main>

      {form && <FormModal form={form} busy={formBusy} onClose={() => !formBusy && setForm(null)} onSubmit={submitForm} />}
      {toast && <div className="toast"><CheckCircle2 size={17} />{toast}<button onClick={() => setToast("")} aria-label="Dismiss"><X size={15} /></button></div>}
    </div>
  );
}

function pageDescription(page: PageKey) {
  return ({
    Overview: "A quick look at your scholarship program.",
    Applicants: "Manage applicant profiles, contact information, and archive status.",
    Applications: "Track applications, eligibility details, and workflow status.",
    "AI Screening": "Run and review saved AI-assisted screening recommendations.",
    Interviews: "Schedule interviews and record their official results.",
    Decisions: "Record and review final scholarship decisions.",
  } as Record<PageKey, string>)[page];
}

function Dashboard({ data, rows, loading, onOpen }: { data: Row | null; rows: Row[]; loading: boolean; onOpen: (p: PageKey) => void }) {
  const stats = data?.stats || {};
  const counts: Record<string, number> = data?.statusCounts || {};
  const maxCount = Math.max(1, ...Object.values(counts).map(Number));

  const cards = [
    { label: "Total applicants", value: stats.applicants ?? "—", note: "Active applicant profiles", icon: Users, tone: "blue" },
    { label: "Applications", value: stats.applications ?? "—", note: "Active scholarship records", icon: FileText, tone: "violet" },
    { label: "Pending review", value: stats.pending ?? "—", note: "Applications needing attention", icon: Clock3, tone: "amber" },
    { label: "Approved scholars", value: stats.approved ?? "—", note: "Recorded approval decisions", icon: Award, tone: "green" },
  ];

  return (
    <>
      <section className="welcome-banner">
        <div className="welcome-content">
          <div className="welcome-tag"><Sparkles size={14} /> LOCAL SCHOLARSHIP WORKSPACE</div>
          <h2>Every opportunity starts<br />with a fair review.</h2>
          <p>Manage applicants, monitor screening recommendations, and keep every scholarship decision documented.</p>
          <button className="welcome-button" onClick={() => onOpen("Applications")}>View applications <ArrowRight size={16} /></button>
        </div>
        <div className="welcome-art">
          <div className="art-ring ring-one" />
          <div className="art-ring ring-two" />
          <div className="art-card">
            <div className="art-card-top"><div className="art-cap"><GraduationCap size={25} /></div><span>STUDENT SUCCESS</span></div>
            <div className="art-line long" />
            <div className="art-line medium" />
            <div className="art-card-bottom">
              <div>
                <small>Review progress</small>
                <strong>{stats.applications ? Math.round((Number(stats.approved || 0) / Math.max(1, Number(stats.applications))) * 100) : 0}%</strong>
              </div>
              <div className="mini-bars"><i /><i /><i /><i /><i /><i /><i /></div>
            </div>
          </div>
          <div className="welcome-orb orb-one" />
          <div className="welcome-orb orb-two" />
        </div>
      </section>

      <section className="stats-grid">
        {cards.map(c => {
          const Icon = c.icon;
          return (
            <div className="stat-card" key={c.label}>
              <div className="stat-top"><span className="stat-label">{c.label}</span><span className={`stat-icon ${c.tone}`}><Icon size={18} /></span></div>
              <div className="stat-value">{loading ? <span className="skeleton">&nbsp;</span> : c.value}</div>
              <div className="stat-foot"><span className="stat-note">{c.note}</span><span className="stat-arrow"><ArrowRight size={14} /></span></div>
            </div>
          );
        })}
      </section>

      <section className="dashboard-lower">
        <div className="panel status-panel">
          <div className="panel-heading">
            <div><h3>Application status</h3><p>Distribution across current statuses</p></div>
            <div className="panel-icon"><Activity size={18} /></div>
          </div>
          {loading ? <LoadingRows /> : Object.keys(counts).length ? (
            <div className="status-list">
              {Object.entries(counts).sort((a, b) => Number(b[1]) - Number(a[1])).slice(0, 7).map(([label, value]) => (
                <div className="status-row" key={label}>
                  <div className="status-label"><span className={`legend-dot ${statusTone(label)}`} /><span>{nice(label)}</span><b>{Number(value)}</b></div>
                  <div className="progress-track"><div className={`progress-fill ${statusTone(label)}`} style={{ width: `${Number(value) / maxCount * 100}%` }} /></div>
                </div>
              ))}
            </div>
          ) : <EmptyState title="No application data yet" text="Application status counts will appear once records are available." />}
          <button className="panel-link" onClick={() => onOpen("Applications")}>Explore applications <ArrowRight size={15} /></button>
        </div>

        <div className="panel recent-panel">
          <div className="panel-heading">
            <div><h3>Recent applications</h3><p>Latest activity in your program</p></div>
            <button className="icon-button small" onClick={() => onOpen("Applications")} title="View all"><ArrowRight size={17} /></button>
          </div>
          {loading ? <LoadingRows /> : rows.length ? (
            <div className="recent-list">
              {rows.slice(0, 5).map((r, i) => (
                <div className="recent-item" key={r.application_id ?? i}>
                  <div className={`recent-avatar color-${i % 5}`}>{nameOf(r).split(/\s+/).slice(0, 2).map((x: string) => x[0]).join("").toUpperCase()}</div>
                  <div className="recent-main"><strong>{nameOf(r)}</strong><span>{r.scholarship_program || `Application #${r.application_id ?? "—"}`}</span></div>
                  <div className="recent-right"><span className={`status-badge ${statusTone(r.status)}`}>{nice(r.status)}</span><small>{dateText(r.created_at)}</small></div>
                </div>
              ))}
            </div>
          ) : <EmptyState title="Nothing to show yet" text="New application records will appear here." />}
          <button className="panel-link" onClick={() => onOpen("Applications")}>View all applications <ArrowRight size={15} /></button>
        </div>
      </section>

      <section className="tip-banner">
        <div className="tip-icon"><BookOpenCheck size={20} /></div>
        <div><strong>Keep every decision transparent</strong><p>Use screening results as decision support, and review each applicant’s full context before making a final scholarship decision.</p></div>
        <button onClick={() => onOpen("AI Screening")}>Review screening <ArrowRight size={15} /></button>
      </section>
    </>
  );
}

function DataPage(props: {
  page: PageKey;
  rows: Row[];
  loading: boolean;
  search: string;
  setSearch: (s: string) => void;
  refresh: () => void;
  onRegister: () => void;
  onApplicantEdit: (r: Row) => void;
  onApplicantArchive: (r: Row) => void;
  onApplicationEdit: (r: Row) => void;
  onStatus: (r: Row) => void;
  onScreen: (r?: Row) => void;
  onSchedule: (r: Row) => void;
  onInterviewResult: (r: Row) => void;
  onDecision: (r?: Row) => void;
}) {
  const { page, rows, loading, search, setSearch, refresh, onApplicantEdit, onApplicantArchive, onApplicationEdit, onStatus, onScreen, onSchedule, onInterviewResult } = props;

  const columns: Record<PageKey, { key: string; label: string }[]> = {
    Overview: [],
    Applicants: [
      { key: "applicant_id", label: "ID" }, { key: "name", label: "Applicant name" },
      { key: "email", label: "Email address" }, { key: "phone", label: "Phone" },
      { key: "municipality", label: "Municipality" }, { key: "created_at", label: "Date added" },
    ],
    Applications: [
      { key: "application_id", label: "Application ID" }, { key: "applicant_name", label: "Applicant" },
      { key: "scholarship_program", label: "Scholarship program" }, { key: "scholarship_year", label: "School year" },
      { key: "academic_average", label: "Average" }, { key: "status", label: "Status" },
      { key: "created_at", label: "Created" },
    ],
    "AI Screening": [
      { key: "application_id", label: "Application" }, { key: "applicant_name", label: "Applicant" },
      { key: "scholarship_program", label: "Program" }, { key: "predicted_class", label: "Screening outcome" },
      { key: "confidence_score", label: "Confidence" }, { key: "screened_at", label: "Screened at" },
    ],
    Interviews: [
      { key: "reference_no", label: "Reference" }, { key: "applicant_name", label: "Applicant" },
      { key: "scheduled_at", label: "Date & time" }, { key: "location", label: "Location" },
      { key: "status", label: "Status" }, { key: "result", label: "Result" },
    ],
    Decisions: [
      { key: "application_id", label: "Application" }, { key: "applicant_name", label: "Applicant" },
      { key: "scholarship_program", label: "Scholarship program" }, { key: "decision", label: "Decision" },
      { key: "reason", label: "Reason" }, { key: "decided_at", label: "Decision date" },
    ],
  };

  const cols = columns[page] || [];
  const intro = page === "AI Screening"
    ? "Recorded predictions are advisory and must be reviewed by an authorized official."
    : page === "Interviews"
      ? "Schedule endorsed applicants and record interview outcomes."
      : "Live records read from your existing scholarship database.";

  return (
    <section className="panel data-panel">
      <div className="data-toolbar">
        <div><h3>{page === "AI Screening" ? "Screening history" : `${page} records`}</h3><p>{intro}</p></div>
        <div className="toolbar-actions">
          <label className="search-box"><Search size={17} /><input value={search} onChange={e => setSearch(e.target.value)} placeholder={`Search ${page.toLowerCase()}...`} /></label>
          <button className="button-secondary" onClick={refresh}><RefreshCw size={15} /> Refresh</button>
        </div>
      </div>

      {page === "AI Screening" && <div className="notice"><Sparkles size={17} /><span>Run a screening to evaluate an existing application with the saved model. Results are persisted and remain advisory, not a final award/rejection.</span></div>}

      {loading ? <div className="table-loading"><LoaderCircle className="spin" size={24} /><span>Loading records…</span></div> : rows.length ? (
        <div className="table-scroll">
          <table>
            <thead><tr>{cols.map(c => <th key={c.key}>{c.label}</th>)}<th>Actions</th></tr></thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={r.applicant_id ?? r.application_id ?? r.interview_id ?? r.decision_id ?? r.screening_id ?? i}>
                  {cols.map(c => <td key={c.key}>{renderCell(r, c.key, page)}</td>)}
                  <td>
                    <div className="row-actions">
                      {page === "Applicants" && <>
                        <button className="row-action" title="Edit applicant" onClick={() => onApplicantEdit(r)}><Pencil size={14} /> Edit</button>
                        <button className="row-action danger" title="Archive applicant" onClick={() => onApplicantArchive(r)}><Archive size={14} /> Archive</button>
                      </>}
                      {page === "Applications" && <>
                        <button className="row-action" onClick={() => onApplicationEdit(r)}><Pencil size={14} /> Edit</button>
                        <button className="row-action" onClick={() => onStatus(r)}><ListChecks size={14} /> Status</button>
                        <button className="row-action" onClick={() => onScreen(r)}><BrainCircuit size={14} /> Screen</button>
                      </>}
                      {page === "AI Screening" && <button className="row-action" onClick={() => onScreen(r)}><BrainCircuit size={14} /> Screen application</button>}
                      {page === "Interviews" && (
                        r.awaiting_schedule
                          ? <button className="row-action" onClick={() => onSchedule(r)}><CalendarPlus size={14} /> Schedule</button>
                          : ["SCHEDULED", "RESCHEDULED"].includes(String(r.status).toUpperCase())
                            ? <button className="row-action" onClick={() => onInterviewResult(r)}><ClipboardCheck size={14} /> Record result</button>
                            : <span className="muted-action">No action</span>
                      )}
                      {page === "Decisions" && <span className="muted-action">Recorded</span>}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : <EmptyState title={search ? "No matching records" : `No ${page.toLowerCase()} found`} text={search ? "Try another search term." : "No matching records are currently available in the database."} />}

      <div className="table-footer">
        <span>Showing <b>{rows.length}</b> record{rows.length === 1 ? "" : "s"}{search ? " matching your search" : ""}</span>
        <span>Source: existing MySQL records</span>
      </div>
    </section>
  );
}

function renderCell(row: Row, key: string, _page: PageKey) {
  if (key === "name" || key === "applicant_name") {
    return (
      <div className="person-cell">
        <div className="table-avatar">{nameOf(row).split(/\s+/).slice(0, 2).map((x: string) => x[0]).join("").toUpperCase()}</div>
        <div><strong>{nameOf(row)}</strong>{row.email && <small>{row.email}</small>}</div>
      </div>
    );
  }

  if (key === "status" || key === "decision" || key === "result" || key === "predicted_class") {
    return <span className={`status-badge ${statusTone(row[key])}`}>{nice(row[key])}</span>;
  }

  if (key === "confidence_score") {
    const n = Number(row[key]);
    return row[key] == null
      ? "—"
      : <span className="confidence"><span className="confidence-track"><i style={{ width: `${Math.max(0, Math.min(1, n <= 1 ? n : n / 100)) * 100}%` }} /></span>{`${Math.round((n <= 1 ? n : n / 100) * 100)}%`}</span>;
  }

  if (["created_at", "decided_at", "scheduled_at", "screened_at", "birth_date"].includes(key)) return dateText(row[key]);
  if (key === "application_id") return <span className="id-cell">{row.reference_no || `APP-${String(row.application_id ?? "").padStart(4, "0")}`}</span>;
  if (key === "applicant_id") return <span className="id-cell">#{row[key]}</span>;
  if (key === "reason") return <span className="reason-cell" title={String(row[key] ?? "")}>{row[key] || "—"}</span>;
  if (key === "academic_average") return row[key] == null ? "—" : `${Number(row[key]).toFixed(2)}%`;

  const value = row[key];
  return value == null || value === "" ? "—" : String(value);
}

function FormModal({ form, busy, onClose, onSubmit }: {
  form: NonNullable<FormState>;
  busy: boolean;
  onClose: () => void;
  onSubmit: (values: Row) => void;
}) {
  const [values, setValues] = useState<Row>(() => ({ ...form.initial }));
  const [error, setError] = useState("");

  const grouped = useMemo(() => {
    const groups: { title: string; fields: Field[] }[] = [];
    for (const field of form.fields) {
      const title = field.section || "Details";
      let group = groups.find(g => g.title === title);
      if (!group) {
        group = { title, fields: [] };
        groups.push(group);
      }
      group.fields.push(field);
    }
    return groups;
  }, [form.fields]);

  const [step, setStep] = useState(0);
  const wizard = form.mode === "register";
  const activeGroup = grouped[Math.min(step, grouped.length - 1)];

  function validateFields(fields: Field[]) {
    for (const f of fields) {
      const value = values[f.key];

      if (f.required && (value === undefined || value === null || String(value).trim() === "")) {
        setError(`${f.label} is required.`);
        return false;
      }

      if (value !== undefined && value !== null && String(value).trim() !== "") {
        if (f.key === "email" && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(value))) {
          setError("Enter a valid email address containing @ and a domain.");
          return false;
        }

        if (f.key === "phone" && !/^\d{11}$/.test(String(value))) {
          setError("Phone number must contain exactly 11 digits.");
          return false;
        }

        if (f.type === "number") {
          const n = Number(value);
          if (!Number.isFinite(n)) {
            setError(`${f.label} must be a valid number.`);
            return false;
          }
          if (f.min !== undefined && n < f.min) {
            setError(`${f.label} must be at least ${f.min}.`);
            return false;
          }
          if (f.max !== undefined && n > f.max) {
            setError(`${f.label} must not exceed ${f.max}.`);
            return false;
          }
          if ([
            "monthly_income", "household", "children_count", "senior_count",
            "pwd_count", "scholars_in_family", "exam_raw_score", "exam_total_items",
          ].includes(f.key) && n < 0) {
            setError(`${f.label} cannot be negative.`);
            return false;
          }
        }
      }
    }

    if (fields.some(f => f.key === "exam_raw_score") && Number(values.exam_raw_score) > Number(values.exam_total_items)) {
      setError("Entrance exam raw score cannot exceed the total number of items.");
      return false;
    }

    setError("");
    return true;
  }

  function submit(e: FormEvent) {
    e.preventDefault();
    setError("");

    if (wizard && step < grouped.length - 1) {
      if (validateFields(activeGroup.fields)) setStep(n => n + 1);
      return;
    }

    if (!validateFields(form.fields)) return;
    onSubmit(values);
  }

  function updateValue(key: string, value: any) {
    setValues(v => {
      const next = { ...v, [key]: value };
      if (key === "exam_total_items" && next.exam_raw_score !== "" && Number(next.exam_raw_score) > Number(value)) {
        next.exam_raw_score = value === "" ? "" : value;
      }
      return next;
    });
    setError("");
  }

  return (
    <div className="modal-backdrop" onMouseDown={e => { if (e.target === e.currentTarget && !busy) onClose(); }}>
      <form className={`modal workflow-modal ${form.mode === "register" ? "wide-modal" : ""}`} onSubmit={submit}>
        <div className="modal-head">
          <div><div className="eyebrow">SCHOLARSHIP MANAGEMENT</div><h2>{form.title}</h2><p>{form.subtitle}</p></div>
          <button type="button" className="icon-button" onClick={onClose} disabled={busy}><X size={18} /></button>
        </div>

        {wizard && (
          <div className="wizard-progress">
            <span>Step {step + 1} of {grouped.length}</span>
            <strong>{activeGroup?.title}</strong>
            <div className="wizard-track"><i style={{ width: `${((step + 1) / grouped.length) * 100}%` }} /></div>
          </div>
        )}

        <div className="form-scroll">
          {(wizard ? (activeGroup ? [activeGroup] : []) : grouped).map(group => (
            <section className="form-section" key={group.title}>
              <h3>{group.title}</h3>
              <div className="form-grid">
                {group.fields.map(field => (
                  <label className={`field-label ${field.type === "checkbox" ? "checkbox-field" : ""} ${field.type === "textarea" ? "full-field" : ""}`} key={field.key}>
                    {field.type === "checkbox" ? (
                      <>
                        <input type="checkbox" checked={Boolean(values[field.key])} onChange={e => updateValue(field.key, e.target.checked)} />
                        <span>{field.label}{field.required ? " *" : ""}</span>
                      </>
                    ) : (
                      <>
                        {field.label}{field.required ? " *" : ""}
                        {field.type === "select" ? (
                          <select required={field.required} value={values[field.key] ?? ""} onChange={e => updateValue(field.key, e.target.value)}>
                            <option value="">Choose…</option>
                            {(field.options || []).map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                          </select>
                        ) : field.type === "textarea" ? (
                          <textarea required={field.required} rows={3} value={values[field.key] ?? ""} placeholder={field.placeholder} onChange={e => updateValue(field.key, e.target.value)} />
                        ) : (
                          <input
                            required={field.required}
                            type={field.type || "text"}
                            min={field.min}
                            max={field.key === "exam_raw_score" && values.exam_total_items !== "" ? Number(values.exam_total_items) : field.max}
                            step={field.step}
                            readOnly={field.readOnly}
                            inputMode={field.key === "phone" ? "numeric" : undefined}
                            maxLength={field.key === "phone" ? 11 : undefined}
                            value={values[field.key] ?? ""}
                            placeholder={field.placeholder}
                            onKeyDown={e => {
                              if (field.key === "phone" && ["-", "+", "e", "E", ".", ","].includes(e.key)) e.preventDefault();
                            }}
                            onChange={e => {
                              let v = e.target.value;
                              if (field.key === "phone") v = v.replace(/\D/g, "").slice(0, 11);
                              if (field.type === "number" && v !== "" && Number(v) < 0) v = v.replace(/-/g, "");
                              updateValue(field.key, v);
                            }}
                          />
                        )}
                      </>
                    )}
                  </label>
                ))}
              </div>
            </section>
          ))}
        </div>

        {error && <div className="form-error">{error}</div>}

        <div className="modal-actions">
          <button
            type="button"
            className="button-secondary"
            onClick={wizard && step > 0 ? () => { setStep(n => n - 1); setError(""); } : onClose}
            disabled={busy}
          >
            {wizard && step > 0 ? "Back" : "Cancel"}
          </button>
          <button className="primary-button" disabled={busy}>
            {busy ? <LoaderCircle size={16} className="spin" /> : null}
            {busy ? "Saving…" : wizard && step < grouped.length - 1 ? "Next" : "Save applicant"}
          </button>
        </div>

        <p className="modal-note"><ShieldCheck size={14} /> Fields marked * are required. Details are validated before saving.</p>
      </form>
    </div>
  );
}

function LoadingRows() {
  return <div className="loading-list">{[1, 2, 3, 4].map(n => <div key={n} className="loading-line"><i /><span /><b /></div>)}</div>;
}

function EmptyState({ title, text }: { title: string; text: string }) {
  return <div className="empty-state"><div className="empty-icon"><FileText size={22} /></div><strong>{title}</strong><p>{text}</p></div>;
}
