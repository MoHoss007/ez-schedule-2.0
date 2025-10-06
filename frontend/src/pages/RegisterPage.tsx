import React, { useState } from "react";
import Shell from "../components/Shell";
import { useAuth } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";


export default function RegisterPage() {
    const { register } = useAuth();
    const nav = useNavigate();
    const [form, setForm] = useState({ email: "", password: "", clubName: "", sport: "", league: "" });
    const [msg, setMsg] = useState("");
    const [busy, setBusy] = useState(false);


    const onSubmit = async (e: React.FormEvent) => {
        e.preventDefault(); setBusy(true);
        const r = await register(form); setBusy(false);
        if (r?.ok) { setMsg(r.message || "Registered! Check your email."); setTimeout(() => nav("/login"), 1200); }
        else setMsg("Registration failed.");
    };
    const bind = (k: keyof typeof form) => ({ value: form[k], onChange: (e: any) => setForm(s => ({ ...s, [k]: e.target.value })) });


    return (
        <Shell>
            <div className="mx-auto max-w-xl">
                <h2 className="mb-6 text-center text-2xl font-semibold text-white">Create your account</h2>
                <form onSubmit={onSubmit} className="space-y-6">
                    <div>
                        <label className="mb-2 block text-sm font-medium text-white">Email</label>
                        <input 
                            className="w-full rounded-lg border-2 border-gray-300 bg-white p-3 text-gray-900 focus:border-[#64BB7E] focus:outline-none focus:ring-2 focus:ring-[#64BB7E]/20" 
                            type="email" 
                            required 
                            {...bind("email")} 
                        />
                    </div>
                    <div>
                        <label className="mb-2 block text-sm font-medium text-white">Password</label>
                        <input 
                            className="w-full rounded-lg border-2 border-gray-300 bg-white p-3 text-gray-900 focus:border-[#64BB7E] focus:outline-none focus:ring-2 focus:ring-[#64BB7E]/20" 
                            type="password" 
                            required 
                            {...bind("password")} 
                        />
                    </div>
                    <div>
                        <label className="mb-2 block text-sm font-medium text-white">Club Name</label>
                        <input 
                            className="w-full rounded-lg border-2 border-gray-300 bg-white p-3 text-gray-900 focus:border-[#64BB7E] focus:outline-none focus:ring-2 focus:ring-[#64BB7E]/20" 
                            required 
                            {...bind("clubName")} 
                        />
                    </div>
                    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                        <div>
                            <label className="mb-2 block text-sm font-medium text-white">Sport</label>
                            <input 
                                className="w-full rounded-lg border-2 border-gray-300 bg-white p-3 text-gray-900 focus:border-[#64BB7E] focus:outline-none focus:ring-2 focus:ring-[#64BB7E]/20" 
                                placeholder="Soccer" 
                                {...bind("sport")} 
                            />
                        </div>
                        <div>
                            <label className="mb-2 block text-sm font-medium text-white">League</label>
                            <input 
                                className="w-full rounded-lg border-2 border-gray-300 bg-white p-3 text-gray-900 focus:border-[#64BB7E] focus:outline-none focus:ring-2 focus:ring-[#64BB7E]/20" 
                                placeholder="YRSL" 
                                {...bind("league")} 
                            />
                        </div>
                    </div>
                    <button 
                        type="submit" 
                        className="w-full rounded-lg bg-[#64BB7E] p-3 font-semibold text-white transition-all hover:bg-[#52a168] hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-[#64BB7E]/50" 
                        disabled={busy}
                    >
                        {busy ? "Creating…" : "Register"}
                    </button>
                    {msg && <p className="text-sm text-white/80">{msg}</p>}
                </form>
            </div>
        </Shell>
    );
}