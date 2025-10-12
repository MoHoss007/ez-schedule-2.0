import { useState } from "react";
import Shell from "../components/Shell";
import { useAuth } from "../context/AuthContext";
import { useCart } from "../context/CartContext";
import { api } from "../lib/api";


export default function PaymentPage() {
    const { user } = useAuth();
    const { selectedTeamIds, subtotal, sport, league } = useCart();
    const [busy, setBusy] = useState(false);


    const pay = async () => {
        setBusy(true);
        const r = await api.createCheckoutSession({ email: user?.email, club: user?.club, items: selectedTeamIds.map((id) => ({ id})) });
        setBusy(false);
        if (r?.ok && r.url) window.location.href = r.url;
    };


    return (
        <Shell>
            <h2 className="mb-6 text-center text-2xl font-semibold text-white">Payment</h2>
            <div className="rounded-lg bg-black/20 p-6 backdrop-blur-sm border border-white/10 max-w-2xl mx-auto">
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                    <div>
                        <div className="text-sm text-white/70">Payer</div>
                        <div className="text-lg text-white">{user?.email}</div>
                    </div>
                    <div>
                        <div className="text-sm text-white/70">Club</div>
                        <div className="text-lg text-white">{user?.club}</div>
                    </div>
                    <div>
                        <div className="text-sm text-white/70">Amount</div>
                        <div className="text-lg text-white">${subtotal.toFixed(2)}</div>
                    </div>
                </div>
                <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2">
                    <div>
                        <div className="text-sm text-white/70">Sport</div>
                        <div className="text-lg text-white">{sport || "—"}</div>
                    </div>
                    <div>
                        <div className="text-sm text-white/70">League</div>
                        <div className="text-lg text-white">{league || "—"}</div>
                    </div>
                </div>
                <button 
                    onClick={pay} 
                    disabled={busy || selectedTeamIds.length === 0} 
                    className={`mt-6 w-full rounded-lg p-3 font-semibold text-white transition-all ${
                        busy || selectedTeamIds.length === 0 
                            ? "bg-gray-400 cursor-not-allowed" 
                            : "bg-[#64BB7E] hover:bg-[#52a168] hover:shadow-lg"
                    }`}
                >
                    {busy ? "Creating Stripe session…" : "Pay with Stripe"}
                </button>
                <div className="mt-3 text-xs text-white/70 text-center">(Demo uses a mock session if backend is unavailable.)</div>
            </div>
        </Shell>
    );
}