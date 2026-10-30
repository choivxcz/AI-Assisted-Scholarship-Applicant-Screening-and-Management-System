import { useEffect, useState } from "react";
import { ClipboardList, Info, LogOut, ShieldCheck } from "lucide-react";

type Props = { user: Record<string, any>; onLogout: () => void; onActivity: () => void };
const text = (value: unknown) => typeof value === "string" && value.trim() ? value.trim() : "Not recorded";

export default function SettingsPage({ user, onLogout, onActivity }: Props) {
  const [tab, setTab] = useState("My account");
  const [compact, setCompact] = useState(() => localStorage.getItem("iskolar-density") === "compact");
  const [darkMode, setDarkMode] = useState(() => localStorage.getItem("iskolar-theme") === "dark");
  const displayName = text(user.display_name || [user.first_name, user.last_name].filter(Boolean).join(" ") || user.username);
  const role = user.role === "ADMIN" ? "Admin" : user.role === "LYDO_OFFICIAL" ? "LYDO Official" : "Not recorded";
  useEffect(() => {
    document.documentElement.dataset.density = compact ? "compact" : "comfortable";
    localStorage.setItem("iskolar-density", compact ? "compact" : "comfortable");
  }, [compact]);
  useEffect(() => {
    document.documentElement.dataset.theme = darkMode ? "dark" : "light";
    localStorage.setItem("iskolar-theme", darkMode ? "dark" : "light");
  }, [darkMode]);

  const profile = <section className="panel">
    <h3>Profile information</h3>
    <p>{displayName} &middot; {role}</p>
    <div className="notice"><Info size={16} />Your staff profile is read-only here. Account details are managed locally by your system administrator.</div>
    <div className="form-grid">{[
      ["First name", text(user.first_name)],
      ["Last name", text(user.last_name)],
      ["Username", text(user.username)],
      ["Role", role],
      ["Work email", "Not recorded"],
      ["Phone", "Not recorded"],
    ].map(([label, value]) => <label className="field-label" key={label}>{label}<input readOnly value={value} /></label>)}</div>
    <p>Admin and LYDO Official accounts share access to the scholarship workspace. Each action is associated with the individual signed-in account.</p>
  </section>;

  const security = <section className="panel">
    <h3>Account &amp; security</h3>
    <p>You are signed in with your individual staff account.</p>
    <div className="settings-security-actions">
      <button className="button-secondary" disabled title="Password changes are not available in this screen">Change password</button>
      <button className="button-secondary" disabled title="Other-session management is not available in this screen">Manage sessions</button>
    </div>
    <p>Contact your system administrator for account or password assistance.</p>
    <div className="notice"><ShieldCheck size={16} />Two-factor authentication is not connected.</div>
  </section>;

  const notifications = <section className="panel">
    <h3>Notification preferences</h3>
    <p>Notification delivery is not connected.</p>
    {[["Application updates", "New submissions and official review changes"], ["Interview scheduling", "Appointments, reschedules, and panel updates"], ["Scholarship decisions", "Officially recorded decisions"], ["Important announcements", "Office-wide notices"], ["Daily digest", "One summary at the end of the workday"]].map(([label, description]) => <label className="preference-row" key={label}><span>{label}<small>{description} &middot; Not connected</small></span><input type="checkbox" disabled /></label>)}
  </section>;

  const preferences = <section className="panel">
    <h3>Workspace preferences</h3>
    <label className="preference-row"><span>Compact tables<small>Saved on this device</small></span><input type="checkbox" checked={compact} onChange={event => setCompact(event.target.checked)} /></label>
    <label className="preference-row"><span>Dark mode<small>Saved on this device</small></span><input type="checkbox" checked={darkMode} onChange={event => setDarkMode(event.target.checked)} /></label>
    <dl className="settings-details">
      <div><dt>Appearance</dt><dd>{darkMode ? "Dark" : "Light"}</dd></div>
      <div><dt>Language</dt><dd>English</dd></div>
      <div><dt>Time zone</dt><dd>Asia/Manila &middot; UTC+08:00</dd></div>
      <div><dt>Default landing page</dt><dd>Overview</dd></div>
    </dl>
  </section>;

  const sessions = <section className="panel">
    <h3>Activity &amp; current session</h3>
    <dl className="settings-details">
      <div><dt>Signed in as</dt><dd>{displayName}</dd></div>
      <div><dt>Username</dt><dd>{text(user.username)}</dd></div>
      <div><dt>Role</dt><dd>{role}</dd></div>
      <div><dt>This device</dt><dd>Local desktop workspace</dd></div>
      <div><dt>Session</dt><dd>Authenticated</dd></div>
    </dl>
    <p>Open the Activity Log to monitor who processed records and when.</p>
    <div className="settings-security-actions">
      <button className="button-secondary" onClick={onActivity}><ClipboardList size={16} />View Activity Log</button>
      <button className="button-secondary" onClick={onLogout}><LogOut size={16} />Sign out</button>
    </div>
  </section>;

  return <div className="settings-page">
    <div className="settings-banner"><h2>Settings</h2><p>Your account, preferences, and workspace</p></div>
    <div className="settings-tabs" role="tablist" aria-label="Settings sections">{["My account", "Preferences", "Activity & sessions"].map(value => <button id={`settings-${value.split(" ")[0]}`} role="tab" aria-selected={tab === value} aria-controls="settings-content" className={tab === value ? "active" : ""} key={value} onClick={() => setTab(value)}>{value}</button>)}</div>
    <div id="settings-content" role="tabpanel" aria-labelledby={`settings-${tab.split(" ")[0]}`} className="settings-grid">
      {tab === "My account" ? <><div>{profile}{security}</div><div>{notifications}{preferences}{sessions}</div></> : tab === "Preferences" ? <><div>{preferences}</div><div>{notifications}</div></> : <div>{sessions}{security}</div>}
    </div>
  </div>;
}
