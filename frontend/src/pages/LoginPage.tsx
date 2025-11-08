import React, { useState } from "react";
import Shell from "../components/Shell";
import { useAuth } from "../context/AuthContext";
import { useNavigate, useLocation } from "react-router-dom";

export default function LoginPage() {
    const { login } = useAuth();
    const nav = useNavigate();
    const location = useLocation();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [err, setErr] = useState("");

    // Get the page user was trying to access, or default to dashboard
    const from = location.state?.from?.pathname || '/dashboard';

    const onSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        const ok = await login(email, password);
        if (ok) {
            // Redirect to the page they were trying to access
            nav(from, { replace: true });
        } else {
            setErr("Invalid credentials");
        }
    };

    return (
        <Shell>
            <div className="min-h-[70vh] flex items-center justify-center">
                <div className="w-full max-w-md rounded-2xl border border-white/10 bg-black/30 p-6 shadow-xl backdrop-blur">
                    <h2 className="mb-2 text-center text-2xl font-semibold">Welcome back</h2>
                    <p className="mb-6 text-center text-sm text-white/80">
                        Sign in to manage your club and teams.
                    </p>

                    <form onSubmit={onSubmit} className="space-y-4">
                        <div>
                            <label className="mb-2 block text-sm">Email</label>
                            <input
                                className="w-full rounded-lg border border-white/20 bg-white p-3 text-gray-900 focus:border-[#64BB7E] focus:outline-none focus:ring-2 focus:ring-[#64BB7E]/30"
                                type="email"
                                required
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                placeholder="you@club.org"
                            />
                        </div>
                        <div>
                            <label className="mb-2 block text-sm">Password</label>
                            <input
                                className="w-full rounded-lg border border-white/20 bg-white p-3 text-gray-900 focus:border-[#64BB7E] focus:outline-none focus:ring-2 focus:ring-[#64BB7E]/30"
                                type="password"
                                required
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="••••••••"
                            />
                        </div>

                        <button
                            type="submit"
                            className="w-full rounded-lg bg-[#64BB7E] p-3 font-semibold text-white transition-all hover:bg-[#52a168] hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-[#64BB7E]/50"
                        >
                            Login
                        </button>
                        {err && <p className="text-center text-sm text-red-300">{err}</p>}
                        <p className="text-center text-sm text-white/80 mt-4">
                            Don’t have an account?{" "}
                            <a
                                href="/register"
                                className="text-[#64BB7E] font-semibold hover:underline"
                            >
                                Sign up now
                            </a>
                        </p>
                    </form>
                </div>
            </div>
        </Shell>
    );
}
