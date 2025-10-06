import React, { useState } from "react";
import Shell from "../components/Shell";
import { useAuth } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";


export default function LoginPage() {
    const { login } = useAuth();
    const nav = useNavigate();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [err, setErr] = useState("");


    const onSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        const ok = await login(email, password);
        if (ok) nav("/dashboard"); else setErr("Invalid credentials");
    };


    return (
        <Shell>
            <div className="mx-auto max-w-md">
                <h2 className="mb-6 text-center text-2xl font-semibold text-white">Welcome back</h2>
                <form onSubmit={onSubmit} className="space-y-6">
                    <div>
                        <label className="mb-2 block text-sm font-medium text-white">Email</label>
                        <input 
                            className="w-full rounded-lg border-2 border-gray-300 bg-white p-3 text-gray-900 focus:border-[#64BB7E] focus:outline-none focus:ring-2 focus:ring-[#64BB7E]/20" 
                            type="email" 
                            required 
                            value={email} 
                            onChange={(e) => setEmail(e.target.value)} 
                        />
                    </div>
                    <div>
                        <label className="mb-2 block text-sm font-medium text-white">Password</label>
                        <input 
                            className="w-full rounded-lg border-2 border-gray-300 bg-white p-3 text-gray-900 focus:border-[#64BB7E] focus:outline-none focus:ring-2 focus:ring-[#64BB7E]/20" 
                            type="password" 
                            required 
                            value={password} 
                            onChange={(e) => setPassword(e.target.value)} 
                        />
                    </div>
                    <button 
                        type="submit" 
                        className="w-full rounded-lg bg-[#64BB7E] p-3 font-semibold text-white transition-all hover:bg-[#52a168] hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-[#64BB7E]/50"
                    >
                        Login
                    </button>
                    {err && <p className="text-sm text-red-400">{err}</p>}
                </form>
            </div>
        </Shell>
    );
}