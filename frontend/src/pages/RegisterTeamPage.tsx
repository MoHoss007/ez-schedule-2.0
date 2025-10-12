import React from "react";
import Shell from "../components/Shell";
import { useCart } from "../context/CartContext";


export default function RegisterTeamPage() {
    const { sport, league, setSport, setLeague, teams, loadTeams, selectedTeamIds, toggleTeam, count, subtotal } = useCart();
    const [loading, setLoading] = React.useState(false);


    const doLoad = async () => { setLoading(true); await loadTeams(sport, league); setLoading(false); };


    return (
        <Shell>
            <h2 className="mb-6 text-center text-2xl font-semibold text-white">Register teams</h2>
            <div className="grid gap-6 md:grid-cols-3">
                <div className="rounded-lg bg-black/20 p-6 md:col-span-2 backdrop-blur-sm border border-white/10">
                    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                        <div>
                            <label className="mb-2 block text-sm font-medium text-white">Sport</label>
                            <input 
                                className="w-full rounded-lg border-2 border-gray-300 bg-white p-3 text-gray-900 focus:border-[#64BB7E] focus:outline-none focus:ring-2 focus:ring-[#64BB7E]/20" 
                                placeholder="Soccer" 
                                value={sport} 
                                onChange={(e) => setSport(e.target.value)} 
                            />
                        </div>
                        <div>
                            <label className="mb-2 block text-sm font-medium text-white">League</label>
                            <input 
                                className="w-full rounded-lg border-2 border-gray-300 bg-white p-3 text-gray-900 focus:border-[#64BB7E] focus:outline-none focus:ring-2 focus:ring-[#64BB7E]/20" 
                                placeholder="YRSL" 
                                value={league} 
                                onChange={(e) => setLeague(e.target.value)} 
                            />
                        </div>
                    </div>
                    <div className="mt-4">
                        <button 
                            onClick={doLoad} 
                            disabled={!sport || !league || loading} 
                            className="rounded-lg bg-[#64BB7E] px-6 py-3 font-semibold text-white transition-all hover:bg-[#52a168] hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-[#64BB7E]/50 disabled:bg-gray-400 disabled:cursor-not-allowed"
                        >
                            {loading ? "Loading…" : "Load teams from database"}
                        </button>
                    </div>

                    {teams.length > 0 && (
                        <div className="mt-6 space-y-3">
                            <div className="text-sm text-white/70">Select teams to register ($0.50 per team)</div>
                            {teams.map(t => {
                                const checked = selectedTeamIds.includes(t.id);
                                return (
                                    <label key={t.id} className="flex items-center justify-between rounded-lg border border-white/20 bg-white/5 p-4 hover:bg-white/10 cursor-pointer transition-colors">
                                        <div className="flex items-center gap-3">
                                            <input 
                                                type="checkbox" 
                                                checked={checked} 
                                                onChange={(e) => toggleTeam(t.id, e.target.checked)} 
                                                className="h-4 w-4 text-[#64BB7E] border-gray-300 rounded focus:ring-[#64BB7E]"
                                            />
                                            <span className="text-white">{t.name}</span>
                                        </div>
                                        <span className="text-sm text-white/70">ID: {t.id}</span>
                                    </label>
                                );
                            })}
                        </div>
                    )}
                </div>

                <div className="rounded-lg bg-black/20 p-6 backdrop-blur-sm border border-white/10">
                    <div className="text-lg font-semibold text-white">Summary</div>
                    <div className="mt-4 flex items-center justify-between text-white">
                        <span>Teams selected</span>
                        <span className="text-xl font-semibold">{count}</span>
                    </div>
                    <div className="flex items-center justify-between text-white">
                        <span>Subtotal</span>
                        <span className="text-xl font-semibold">${subtotal.toFixed(2)}</span>
                    </div>
                    <a 
                        className={`mt-4 block w-full rounded-lg bg-[#64BB7E] p-3 text-center font-semibold text-white transition-all hover:bg-[#52a168] hover:shadow-lg ${count === 0 ? "pointer-events-none opacity-50" : ""}`} 
                        href="/checkout"
                    >
                        Continue to checkout
                    </a>
                    <div className="mt-3 text-xs text-white/70">Selections are saved. You can navigate away and come back later.</div>
                </div>
            </div>
        </Shell>
    );
}