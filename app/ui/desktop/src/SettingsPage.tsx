import { useEffect, useState } from "react";
import { ClipboardList, Info } from "lucide-react";

type Props = { onActivity: () => void };

export default function SettingsPage({ onActivity }: Props) {
  const [tab, setTab] = useState("Preferences");
  const [compact, setCompact] = useState(() => localStorage.getItem("iskolar-density") === "compact");
  const [darkMode, setDarkMode] = useState(() => localStorage.getItem("iskolar-theme") === "dark");
  useEffect(() => {
    document.documentElement.dataset.density = compact ? "compact" : "comfortable";
    localStorage.setItem("iskolar-density", compact ? "compact" : "comfortable");
  }, [compact]);
  useEffect(() => {
    document.documentElement.dataset.theme = darkMode ? "dark" : "light";
    localStorage.setItem("iskolar-theme", darkMode ? "dark" : "light");
  }, [darkMode]);

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
    <h3>Local workspace</h3>
    <div className="notice"><Info size={16} />Login is disabled. New actions are not associated with an individual staff account.</div>
    <p>The Activity Log shows previously recorded activity. New staff activity entries are not recorded while login is disabled.</p>
    <button className="button-secondary" onClick={onActivity}><ClipboardList size={16} />View Activity Log</button>
  </section>;

  return <div className="settings-page">
    <div className="settings-banner"><h2>Settings</h2><p>Your preferences and local workspace</p></div>
    <div className="settings-tabs" role="tablist" aria-label="Settings sections">{["Preferences", "Workspace"].map(value => <button id={`settings-${value.split(" ")[0]}`} role="tab" aria-selected={tab === value} aria-controls="settings-content" className={tab === value ? "active" : ""} key={value} onClick={() => setTab(value)}>{value}</button>)}</div>
    <div id="settings-content" role="tabpanel" aria-labelledby={`settings-${tab.split(" ")[0]}`} className="settings-grid">
      {tab === "Preferences" ? <><div>{preferences}</div><div>{notifications}</div></> : <div>{sessions}</div>}
    </div>
  </div>;
}
