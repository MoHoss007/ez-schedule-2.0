import React from "react";
import Shell from "../components/Shell";
import { useCart } from "../context/CartContext";
import { useAuth } from "../context/AuthContext";


export default function CheckoutPage() {
    const { sport, league, selectedTeamIds, subtotal } = useCart();
    const { user } = useAuth();


    return (
        <Shell>
            <h2 className="mb-6 text-center text-2xl font-semibold text-white">Checkout</h2>
            <div className="grid gap-6 md:grid-cols-3">
                <div className="rounded-lg bg-black/20 p-6 md:col-span-2 backdrop-blur-sm border border-white/10">
                    <div>
                        <div className="text-sm text-white/70">Club</div>
                        <div className="text-lg font-medium text-white">{user?.club || "Your Club"}</div>
                        <div className="text-sm text-white/80">{user?.email || "email@example.com"}</div>
                    </div>
                    <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
                        <div>
                            <div className="text-sm text-white/70">Sport</div>
                            <div className="text-lg text-white">{sport || "—"}</div>
                        </div>
                        <div>
                            <div className="text-sm text-white/70">League</div>
                            <div className="text-lg text-white">{league || "—"}</div>
                        </div>
                        <div>
                            <div className="text-sm text-white/70">Teams Selected</div>
                            <div className="text-lg text-white">{selectedTeamIds.length}</div>
                        </div>
                    </div>
                    <div className="mt-6">
                        <div className="text-sm text-white/70">Team IDs</div>
                        <div className="text-xs text-white/80">{selectedTeamIds.join(", ") || "—"}</div>
                    </div>
                </div>
                <div className="rounded-lg bg-black/20 p-6 backdrop-blur-sm border border-white/10">
                    <div className="text-lg font-semibold text-white">Payment</div>
                    <div className="mt-4 flex items-center justify-between text-white">
                        <span>Subtotal</span>
                        <span className="text-xl font-semibold">${subtotal.toFixed(2)}</span>
                    </div>
                    <a 
                        className="mt-4 block w-full rounded-lg bg-[#64BB7E] p-3 text-center font-semibold text-white transition-all hover:bg-[#52a168] hover:shadow-lg" 
                        href="/payment"
                    >
                        Proceed to payment
                    </a>
                </div>
            </div>
        </Shell>
    );
}