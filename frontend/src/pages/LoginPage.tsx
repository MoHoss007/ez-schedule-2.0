// src/pages/LoginPage.tsx
import React, { useState } from "react";
import { Shell } from "../components/Shell";
import { useAuth } from "../context/AuthContext";
import { useNavigate, useLocation, Link } from "react-router-dom";

export default function LoginPage() {
  const { login } = useAuth();
  const nav = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");

  const from = location.state?.from?.pathname || "/dashboard";

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const ok = await login(email, password);
    if (ok) {
      nav(from, { replace: true });
    } else {
      setErr("Invalid credentials");
    }
  };

  return (
    <Shell>
      <div className="auth-wrap">
        <div className="auth-card">
          <h2 className="mb-2 text-2xl font-semibold">Welcome back</h2>
          <p className="mb-6 text-sm text-white/80">
            Sign in to manage your club and teams.
          </p>

          <form onSubmit={onSubmit} className="auth-form">
            <div className="auth-field">
              <label className="auth-label">Email</label>
              <input
                className="auth-input"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@club.org"
              />
            </div>

            <div className="auth-field">
              <label className="auth-label">Password</label>
              <input
                className="auth-input"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
              />
            </div>

            <button type="submit" className="auth-submit-btn">
              Log in
            </button>

            {err && <p className="auth-error">{err}</p>}

            <p className="auth-switch">
              Don’t have an account?{" "}
              <Link to="/register" className="auth-link">
                Get started
              </Link>
            </p>
          </form>
        </div>
      </div>
    </Shell>
  );
}
