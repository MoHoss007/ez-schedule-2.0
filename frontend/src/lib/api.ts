import { SignatureV4 } from "@aws-sdk/signature-v4";
import { Sha256 } from "@aws-crypto/sha256-js";
import { HttpRequest } from "@aws-sdk/protocol-http";

const AWS_ACCESS_KEY_ID     = import.meta.env.VITE_AWS_ACCESS_KEY_ID!;
const AWS_SECRET_ACCESS_KEY = import.meta.env.VITE_AWS_SECRET_ACCESS_KEY!;
const AWS_SESSION_TOKEN     = import.meta.env.VITE_AWS_SESSION_TOKEN || undefined; // if using temp creds
const AWS_REGION            = import.meta.env.VITE_AWS_REGION!;
const AWS_SERVICE           = import.meta.env.VITE_AWS_SERVICE!; // e.g. "execute-api" (API Gateway), "lambda" (Function URL), "s3", etc.


const credentials = {
  accessKeyId: AWS_ACCESS_KEY_ID,
  secretAccessKey: AWS_SECRET_ACCESS_KEY,
  sessionToken: AWS_SESSION_TOKEN,
};

const signer = new SignatureV4({
  credentials,
  region: AWS_REGION,
  service: AWS_SERVICE,
  sha256: Sha256,
});

export const API_BASE = import.meta.env.VITE_API_BASE_URL;
export const PRICE_PER_TEAM = parseFloat(import.meta.env.VITE_PRICE_PER_TEAM || "0.5"); // $0.50

console.log("API_BASE:", API_BASE);

export async function getAWSHeaders(method: string, url: string, body?: string) {
  const u = new URL(url);

  // Build an AWS HttpRequest
  const request = new HttpRequest({
    protocol: u.protocol,
    hostname: u.hostname,
    port: u.port ? Number(u.port) : undefined,
    method,
    path: u.pathname + u.search, // must include canonical query
    headers: {
      host: u.host,
      // Keep JSON by default; adjust if you send other content types.
      "content-type": "application/json"
    },
    body, // signer will hash the payload
  });

  // Produce SigV4-signed request (adds Authorization, X-Amz-Date, etc.)
  const signed = await signer.sign(request);

  // Return headers for fetch()
  // Note: fetch will set Content-Length for you
  const h: Record<string, string> = {};
  for (const [k, v] of Object.entries(signed.headers)) {
    if (typeof v === "string") h[k] = v;
  }
  return h;
}


export const api = {
    async register(payload: { email: string; password: string; username: string }) {
        console.log("API register call to:", `${API_BASE}/api/v1/users/signup`);
        console.log("Payload:", payload);
        
        try {
            const headers = await getAWSHeaders("POST", `${API_BASE}/api/v1/users/signup`, JSON.stringify(payload));
            const res = await fetch(`${API_BASE}/api/v1/users/signup`, {
                method: "POST",
                headers,
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
        console.log("API login call to:", `${API_BASE}/api/v1/users/login`);
        console.log("Login payload:", payload);
        
        try {
            const headers = await getAWSHeaders("POST", `${API_BASE}/api/v1/users/login`, JSON.stringify(payload));
            console.log("Request headers:", headers);
            
            const res = await fetch(`${API_BASE}/api/v1/users/login`, {
                method: "POST",
                headers,
                credentials: "include",
                body: JSON.stringify(payload),
            });
            
            console.log("Login response status:", res.status);
            console.log("Login response headers:", Object.fromEntries(res.headers.entries()));
            
            if (!res.ok) {
                const errorText = await res.text();
                console.error("Login API Error - Status:", res.status);
                console.error("Login API Error - Response:", errorText);
                throw new Error(`Login failed: ${res.status} - ${errorText}`);
            }
            
            // Check if response is actually JSON
            const contentType = res.headers.get("content-type");
            console.log("Response content-type:", contentType);
            
            if (!contentType || !contentType.includes("application/json")) {
                const responseText = await res.text();
                console.error("Non-JSON response received:", responseText);
                throw new Error(`Expected JSON but got: ${contentType}. Response: ${responseText.substring(0, 200)}...`);
            }
            
            const result = await res.json();
            console.log("Login API Response:", result);
            return result;
        } catch (error) {
            console.error("Login Network/API Error:", error);
            throw error;
        }
    },
    async me() {
        console.log("API me call to:", `${API_BASE}/api/v1/users/me`);
        
        try {
            const headers = await getAWSHeaders("GET", `${API_BASE}/api/v1/users/me`);
            console.log("Request headers:", headers);
            
            const res = await fetch(`${API_BASE}/api/v1/users/me`, {
                headers,
                credentials: "include",
            });
            
            console.log("Me response status:", res.status);
            console.log("Me response headers:", Object.fromEntries(res.headers.entries()));
            
            if (!res.ok) {
                const errorText = await res.text();
                console.error("Me API Error - Status:", res.status);
                console.error("Me API Error - Response:", errorText);
                throw new Error(`Me check failed: ${res.status} - ${errorText}`);
            }
            
            // Check if response is actually JSON
            const contentType = res.headers.get("content-type");
            console.log("Response content-type:", contentType);
            
            if (!contentType || !contentType.includes("application/json")) {
                const responseText = await res.text();
                console.error("Non-JSON response received:", responseText);
                throw new Error(`Expected JSON but got: ${contentType}. Response: ${responseText.substring(0, 200)}...`);
            }
            
            const result = await res.json();
            console.log("Me API Response:", result);
            return result;
        } catch (error) {
            console.error("Me Network/API Error:", error);
            throw error;
        }
    },
    async refresh() {
        const headers = await getAWSHeaders("POST", `${API_BASE}/api/v1/users/refresh`);
        const res = await fetch(`${API_BASE}/api/v1/users/refresh`, {
            method: "POST",
            headers,
            credentials: "include",
        });
        if (!res.ok) throw new Error("Refresh failed");
        return await res.json();
    },
    async logout() {
        const headers = await getAWSHeaders("POST", `${API_BASE}/api/v1/users/logout`);
        await fetch(`${API_BASE}/api/v1/users/logout`, {
            method: "POST",
            headers,
            credentials: "include",
        });
    },
    async listTeams(params: { sport: string; league: string }) {
        const { sport, league } = params;
        try {
            const url = `${API_BASE}/clubs/teams?sport=${encodeURIComponent(sport)}&league=${encodeURIComponent(league)}`;
            const headers = await getAWSHeaders("GET", url);
            const res = await fetch(url, {
                headers,
                credentials: "include",
            });
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
        const body = JSON.stringify({ email, club, items });
        const headers = await getAWSHeaders("POST", `${API_BASE}/billing/create-checkout-session`, body);
        const res = await fetch(`${API_BASE}/billing/create-checkout-session`, {
            method: "POST",
            headers,
            credentials: "include", // if you use cookies for auth; safe otherwise
            body,
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