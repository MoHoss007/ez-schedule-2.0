// src/pages/RegisterPage.tsx
import React, { useState } from "react";
import { Shell } from "../components/Shell";
import { useAuth } from "../context/AuthContext";
import { useNavigate, Link } from "react-router-dom";

export default function RegisterPage() {
  const { register } = useAuth();
  const nav = useNavigate();
  const [form, setForm] = useState({
    email: "",
    username: "",
    password: "",
  });
  const [msg, setMsg] = useState("");
  const [busy, setBusy] = useState(false);

  const bind = (key: keyof typeof form) => ({
    value: form[key],
    onChange: (e: React.ChangeEvent<HTMLInputElement>) =>
      setForm((prev) => ({ ...prev, [key]: e.target.value })),
  });

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    const ok = await register(form);
    setBusy(false);

    if (ok) {
      setMsg("Registration successful! Redirecting…");
      setTimeout(() => nav("/dashboard"), 1200);
    } else {
      setMsg("Registration failed. Please try again.");
    }
  };

  return (
    <Shell>
      <div className="auth-wrap">
        <div className="auth-card">
          <h2 className="mb-2 text-2xl font-semibold">Create your account</h2>
          <p className="mb-6 text-sm text-white/80">
            Start syncing your schedules to TeamSnap in minutes.
          </p>

          <form onSubmit={onSubmit} className="auth-form">
            <div className="auth-field">
              <label className="auth-label">Email</label>
              <input
                className="auth-input"
                type="email"
                required
                placeholder="you@club.org"
                {...bind("email")}
              />
            </div>

            <div className="auth-field">
              <label className="auth-label">Username</label>
              <input
                className="auth-input"
                type="text"
                required
                placeholder="Club admin name"
                {...bind("username")}
              />
            </div>

            <div className="auth-field">
              <label className="auth-label">Password</label>
              <input
                className="auth-input"
                type="password"
                required
                placeholder="Choose a secure password"
                {...bind("password")}
              />
            </div>

            <button
              type="submit"
              disabled={busy}
              className="auth-submit-btn"
            >
              {busy ? "Creating…" : "Get started"}
            </button>

            {msg && <p className="auth-message">{msg}</p>}

            <p className="auth-switch">
              Already have an account?{" "}
              <Link to="/login" className="auth-link">
                Log in here
              </Link>
            </p>
          </form>
        </div>
      </div>
    </Shell>
  );
}
