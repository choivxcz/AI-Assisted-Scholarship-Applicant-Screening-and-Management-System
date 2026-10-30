import { FormEvent, useState } from "react";
import { ArrowRight, Eye, EyeOff, FolderCheck, LoaderCircle, ShieldCheck, UserRound, Users } from "lucide-react";

type Props = { onLogin: (username: string, password: string) => Promise<void> };

export default function LoginPage({ onLogin }: Props) {
  const [visible, setVisible] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    setError("");
    const data = new FormData(event.currentTarget);
    const username = String(data.get("username") || "").trim();
    const password = String(data.get("password") || "");
    if (!username || !password) {
      setError("Enter your username and password.");
      return;
    }
    setBusy(true);
    try {
      await onLogin(username, password);
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : "Sign-in could not be completed. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  return <main className="auth-shell auth-login">
    <section className="auth-brand">
      <div className="official-logos">
        <img src="/assets/stc.png" alt="Bayan ng Santa Cruz" />
        <img src="/assets/lydo.png" alt="Local Youth Development Office Santa Cruz Laguna" />
      </div>
      <div className="brand-name">iskolar.</div>
      <small>NG BAYAN &middot; SCHOLARSHIP MANAGEMENT</small>
      <p className="auth-office">LOCAL YOUTH DEVELOPMENT OFFICE</p>
      <h1>Fair opportunities.<br />A brighter Santa Cruz.</h1>
      <p>An organized, transparent workspace for scholarship applications, thoughtful review, and accountable decisions for the youth of Santa Cruz.</p>
      <div className="auth-benefits">
        <p><FolderCheck size={20} aria-hidden="true" /><span><strong>Organized records</strong><small>One shared workspace, accountable individual actions.</small></span></p>
        <p><ShieldCheck size={20} aria-hidden="true" /><span><strong>Fair and official</strong><small>Final decisions remain with authorized LYDO officials.</small></span></p>
        <p><Users size={20} aria-hidden="true" /><span><strong>Better collaboration</strong><small>Coordinate screening, interviews, and scholarship review.</small></span></p>
      </div>
      <footer>Investing in people, building a brighter Santa Cruz tomorrow.<br />Santa Cruz, Laguna</footer>
    </section>
    <section className="auth-form-area">
      <form className="auth-form" onSubmit={submit} aria-busy={busy}>
        <div className="eyebrow">&bull; Authorized scholarship workspace</div>
        <h2>Welcome back</h2>
        <p>Sign in to support the next generation of Santa Cruz scholars.</p>
        <label className="field-label">Username
          <div className="username-input">
            <input name="username" required maxLength={50} autoComplete="username" autoCapitalize="none" spellCheck={false} disabled={busy} placeholder="Enter your username" />
            <UserRound size={16} aria-hidden="true" />
          </div>
        </label>
        <label className="field-label">Password
          <div className="password-input">
            <input name="password" required autoComplete="current-password" disabled={busy} type={visible ? "text" : "password"} placeholder="Enter your password" />
            <button type="button" disabled={busy} aria-label={visible ? "Hide password" : "Show password"} aria-pressed={visible} onClick={() => setVisible(value => !value)}>
              {visible ? <Eye size={16} /> : <EyeOff size={16} />}
            </button>
          </div>
        </label>
        <div className="auth-options">
          <button type="button" disabled={busy} onClick={() => setError("Please contact your LYDO administrator for sign-in assistance.")}>Need sign-in help?</button>
        </div>
        {error && <div className="form-error" role="alert">{error}</div>}
        <button className="primary-button" type="submit" disabled={busy}>
          {busy && <LoaderCircle className="spin" size={16} aria-hidden="true" />}
          {busy ? "Signing in..." : "Sign In"}<ArrowRight size={16} aria-hidden="true" />
        </button>
        <p className="auth-switch">Admin &amp; LYDO Official access</p>
        <div className="auth-staff-notice">
          <div><ShieldCheck size={16} /><strong>For authorized LYDO personnel only</strong></div>
          <p>Admin and LYDO Official accounts use the same scholarship workspace. Use your individual account so processed actions are recorded under your identity.</p>
        </div>
      </form>
    </section>
  </main>;
}
