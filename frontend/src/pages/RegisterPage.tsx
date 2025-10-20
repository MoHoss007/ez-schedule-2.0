import React, { useState } from "react";
import Shell from "../components/Shell";
import { useAuth } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";

export default function RegisterPage() {
  const { register } = useAuth();
  const nav = useNavigate();
  const [form, setForm] = useState({
    email: "",
    password: "",
    username: "",
  });
  const [msg, setMsg] = useState("");
  const [busy, setBusy] = useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    const r = await register(form);
    setBusy(false);
    if (r) {
      setMsg("Registration successful! Redirecting...");
      setTimeout(() => nav("/dashboard"), 1200);
    } else setMsg("Registration failed.");
  };
  const bind = (k: keyof typeof form) => ({
    value: form[k],
    onChange: (e: any) => setForm((s) => ({ ...s, [k]: e.target.value })),
  });

  return (
    <Shell>
      <div className="min-h-[70vh] flex items-center justify-center">
        <div className="w-full max-w-xl rounded-2xl border border-white/10 bg-black/30 p-6 shadow-xl backdrop-blur">
          <h2 className="mb-2 text-center text-2xl font-semibold">Create your account</h2>
          <p className="mb-6 text-center text-sm text-white/80">
            Start syncing your schedules to TeamSnap in minutes.
          </p>

          <form onSubmit={onSubmit} className="space-y-4">
            <div className="grid grid-cols-1 gap-4">
              <div>
                <label className="mb-2 block text-sm">Email</label>
                <input
                  className="w-full rounded-lg border border-white/20 bg-white p-3 text-gray-900 focus:border-[#64BB7E] focus:outline-none focus:ring-2 focus:ring-[#64BB7E]/30"
                  type="email"
                  required
                  {...bind("email")}
                />
              </div>
              <div>
                <label className="mb-2 block text-sm">Username</label>
                <input
                  className="w-full rounded-lg border border-white/20 bg-white p-3 text-gray-900 focus:border-[#64BB7E] focus:outline-none focus:ring-2 focus:ring-[#64BB7E]/30"
                  required
                  {...bind("username")}
                />
              </div>
              <div>
                <label className="mb-2 block text-sm">Password</label>
                <input
                  className="w-full rounded-lg border border-white/20 bg-white p-3 text-gray-900 focus:border-[#64BB7E] focus:outline-none focus:ring-2 focus:ring-[#64BB7E]/30"
                  type="password"
                  required
                  {...bind("password")}
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={busy}
              className="w-full rounded-lg bg-[#64BB7E] p-3 font-semibold text-white transition-all hover:bg-[#52a168] hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-[#64BB7E]/50 disabled:opacity-70"
            >
              {busy ? "Creating…" : "Register"}
            </button>
            {msg && <p className="text-center text-sm text-white/90">{msg}</p>}
          </form>
        </div>
      </div>
    </Shell>
  );
}
