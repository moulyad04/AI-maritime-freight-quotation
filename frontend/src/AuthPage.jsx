import { useState } from "react";
import { signup, login } from "./services/authApi";

const FEATURES = [
  { icon: "🧭", title: "Smart route scoring", text: "Ranks every route by transit time, distance and transshipments." },
  { icon: "💰", title: "Transparent pricing", text: "See base freight, fuel and port charges in every quote." },
  { icon: "🌦️", title: "Weather & customs risk", text: "Know the risks before you commit to a shipment." }
];

function AuthPage({ onAuthSuccess }) {
  const [mode, setMode] = useState("signup");
  const [form, setForm] = useState({
    username: "",
    password: "",
    confirmPassword: ""
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const isSignup = mode === "signup";

  const handleChange = (event) => {
    setForm({
      ...form,
      [event.target.name]: event.target.value
    });
  };

  const switchMode = () => {
    setMode(isSignup ? "login" : "signup");
    setForm({ username: "", password: "", confirmPassword: "" });
    setError("");
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");

    if (isSignup) {
      if (form.password.length < 6) {
        setError("Password must be at least 6 characters.");
        return;
      }
      if (form.password !== form.confirmPassword) {
        setError("Passwords do not match.");
        return;
      }
    }

    setLoading(true);

    try {
      const data = isSignup
        ? await signup(form.username, form.password)
        : await login(form.username, form.password);

      localStorage.setItem("token", data.token);
      localStorage.setItem("username", data.username);
      localStorage.setItem("role", data.role);
      onAuthSuccess(data.username, data.role);
    } catch (err) {
      setError(err.message || "Something went wrong. Is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-shell">
        <div className="auth-showcase">
          <div className="auth-logo">⚓ Maritime Freight</div>
          <h1>AI-powered freight quotations, in seconds.</h1>
          <p className="auth-lede">
            Agents for routing, pricing, weather and customs work
            together to build every quote.
          </p>
          <ul className="feature-list">
            {FEATURES.map((f) => (
              <li key={f.title}>
                <span className="feature-icon">{f.icon}</span>
                <div>
                  <b>{f.title}</b>
                  <span>{f.text}</span>
                </div>
              </li>
            ))}
          </ul>
        </div>

        <div className="auth-card">
          <h2 className="auth-title">
            {isSignup ? "Create your account" : "Welcome back"}
          </h2>
          <p className="auth-subtitle">
            {isSignup
              ? "Start generating quotations in a minute."
              : "Log in to continue to your dashboard."}
          </p>

          <form className="auth-form" onSubmit={handleSubmit}>
            <div className="field">
              <label htmlFor="username">Username</label>
              <input
                id="username"
                name="username"
                value={form.username}
                onChange={handleChange}
                autoComplete="username"
                required
              />
            </div>

            <div className="field">
              <label htmlFor="password">Password</label>
              <input
                id="password"
                name="password"
                type="password"
                value={form.password}
                onChange={handleChange}
                autoComplete={isSignup ? "new-password" : "current-password"}
                required
              />
            </div>

            {isSignup && (
              <div className="field">
                <label htmlFor="confirmPassword">Confirm password</label>
                <input
                  id="confirmPassword"
                  name="confirmPassword"
                  type="password"
                  value={form.confirmPassword}
                  onChange={handleChange}
                  autoComplete="new-password"
                  required
                />
              </div>
            )}

            {error && <p className="form-error">{error}</p>}

            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? "Please wait..." : isSignup ? "Create account" : "Log in"}
            </button>
          </form>

          <div className="auth-switch">
            <span>{isSignup ? "Already have an account?" : "New here?"}</span>
            <button type="button" className="btn-link" onClick={switchMode}>
              {isSignup ? "Log in instead" : "Create an account"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default AuthPage;
