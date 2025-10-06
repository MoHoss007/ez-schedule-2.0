import React from "react";
import Shell from "../components/Shell";


export default function PaymentSuccessPage() {
    return (
        <Shell>
            <div className="mx-auto max-w-lg text-center">
                <div className="mx-auto mb-3 h-12 w-12 rounded-full bg-emerald-500/30" />
                <h2 className="mb-2 text-2xl font-semibold">Payment successful</h2>
                <p className="mb-6 opacity-80">We emailed your receipt and confirmation. Your teams will be activated shortly.</p>
                <a className="rounded-2xl bg-white/10 px-3 py-2 hover:bg-white/20" href="/dashboard">Go to Dashboard</a>
            </div>
        </Shell>
    );
}