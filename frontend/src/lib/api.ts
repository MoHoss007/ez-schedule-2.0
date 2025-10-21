export const API_BASE = "https://ym4cbyfp2us7k5hmvy3wcjslwm0ppdhb.lambda-url.us-east-2.on.aws/";
export const PRICE_PER_TEAM = 0.5; // $0.50


export const api = {
    async register(payload: { email: string; password: string; username: string }) {
        console.log("API register call to:", `${API_BASE}/api/users/signup`);
        console.log("Payload:", payload);
        
        try {
            const res = await fetch(`${API_BASE}/api/users/signup`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                credentials: "include",
                body: JSON.stringify(payload),
            });
            
            console.log("Response status:", res.status);
            console.log("Response headers:", Object.fromEntries(res.headers.entries()));
            
            if (!res.ok) {
                const errorText = await res.text();
                console.error("API Error:", errorText);
                throw new Error(`Signup failed: ${res.status} - ${errorText}`);
            }
            
            const result = await res.json();
            console.log("API Response:", result);
            return result;
        } catch (error) {
            console.error("Network/API Error:", error);
            throw error;
        }
    },
    async login(payload: { email: string; password: string }) {
        const res = await fetch(`${API_BASE}/api/users/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify(payload),
        });
        if (!res.ok) throw new Error("Login failed");
        return await res.json();
    },
    async me() {
        const res = await fetch(`${API_BASE}/api/users/me`, {
            credentials: "include",
        });
        if (!res.ok) throw new Error("Me check failed");
        return await res.json();
    },
    async refresh() {
        const res = await fetch(`${API_BASE}/api/users/refresh`, {
            method: "POST",
            credentials: "include",
        });
        if (!res.ok) throw new Error("Refresh failed");
        return await res.json();
    },
    async logout() {
        await fetch(`${API_BASE}/api/users/logout`, {
            method: "POST",
            credentials: "include",
        });
    },
    async listTeams(params: { sport: string; league: string }) {
        const { sport, league } = params;
        try {
            const res = await fetch(`${API_BASE}/clubs/teams?sport=${encodeURIComponent(sport)}&league=${encodeURIComponent(league)}`);
            if (!res.ok) throw new Error("list teams failed");
            return await res.json();
        } catch {
            return { ok: true, teams: [{ id: 1, name: "U10 Red" }, { id: 2, name: "U12 Green" }, { id: 3, name: "U14 Elite" }, { id: 4, name: "U16 Academy" }] };
        }
    },
    async cancelNextSeason(teamId: number) { return { ok: true }; },
    async createCheckoutSession({
        email,
        club,
        items,
    }: {
        email?: string;
        club?: string;
        items: { id: number}[];
    }) {
        const res = await fetch(`${API_BASE}/billing/create-checkout-session`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include", // if you use cookies for auth; safe otherwise
            body: JSON.stringify({ email, club, items }),
        });
        if (!res.ok) {
            return { ok: false, error: "Failed to create checkout session" };
        }
        return res.json();
    },
};

// ========================= Flask endpoints =========================
// 1) POST /auth/register { email, password, clubName, sport, league } -> { ok, user, message }
// 2) POST /auth/login { email, password } -> { ok, token, user }
// 3) GET /auth/me (Bearer token) -> { ok, user: { email, club, teamsRegistered } }
// 4) GET /clubs/teams?sport=..&league=.. -> { ok, teams: [{id,name}] }
// 5) POST /teams/:id/cancel-next-season -> { ok: true }
// 6) POST /billing/create-checkout-session { email, club, items } -> { ok: true, url }
// success_url should be your SPA route /payment/success