import React, { useState } from "react";
import Shell from "../components/Shell";
import { useAuth } from "../context/AuthContext";
import { api, PRICE_PER_TEAM } from "../lib/api";


export default function DashboardPage() {
    const { user } = useAuth();
    const [teams, setTeams] = useState([
        { id: 1, name: "U10 Red", nextSeasonCanceled: false },
        { id: 2, name: "U12 Green", nextSeasonCanceled: false },
        { id: 3, name: "U14 Elite", nextSeasonCanceled: true },
    ]);


    const cancelTeam = async (id: number) => { await api.cancelNextSeason(id); setTeams(ts => ts.map(t => t.id === id ? { ...t, nextSeasonCanceled: true } : t)); };


    return (
        <Shell>
            <div className="mb-6 flex items-center justify-between">
                <h2 className="text-2xl font-semibold">Dashboard</h2>
                <div className="text-right">
                    <div className="text-xs opacity-70">{user?.club || "Club"}</div>
                    <div className="text-sm font-medium">{user?.email || "email@example.com"}</div>
                </div>
            </div>
            <div className="grid gap-4 sm:grid-cols-3">
                <div className="rounded-lg bg-neutral-800 p-4"><div className="text-sm opacity-70">Teams registered</div><div className="text-3xl font-semibold">{teams.length}</div></div>
                <div className="rounded-lg bg-neutral-800 p-4"><div className="text-sm opacity-70">Next Invoice</div><div className="text-3xl font-semibold">${(teams.length * PRICE_PER_TEAM).toFixed(2)}</div></div>
                <div className="rounded-lg bg-neutral-800 p-4"><div className="text-sm opacity-70">Status</div><div className="text-3xl font-semibold">Active</div></div>
            </div>
            <h3 className="mt-8 mb-3 text-xl font-semibold">Manage teams</h3>
            <div className="space-y-3">
                {teams.map(t => (
                    <div key={t.id} className="flex items-center justify-between rounded-xl border border-neutral-800 bg-neutral-900 p-4">
                        <div><div className="text-lg font-medium">{t.name}</div><div className="text-xs opacity-70">ID: {t.id}</div></div>
                        {t.nextSeasonCanceled ? <span className="text-sm text-emerald-400">Canceled for next season</span> : <button className="rounded-2xl bg-red-500/80 px-3 py-2 text-sm hover:bg-red-500" onClick={() => cancelTeam(t.id)}>Cancel next season</button>}
                    </div>
                ))}
            </div>
        </Shell>
    );
}