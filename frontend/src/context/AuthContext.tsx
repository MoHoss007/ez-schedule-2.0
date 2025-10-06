import React, { createContext, useContext, useEffect, useState } from "react";
import { api } from "../lib/api";
import { readLS, writeLS, removeLS } from "../lib/storage";


interface User { email: string; club?: string; teamsRegistered?: number }
interface AuthCtx {
    token: string;
    user: User | null;
    loading: boolean;
    login: (email: string, password: string) => Promise<boolean>;
    register: (payload: { email: string; password: string; clubName: string; sport: string; league: string }) => Promise<any>;
    logout: () => void;
}


const Ctx = createContext<AuthCtx>({} as any);
export const useAuth = () => useContext(Ctx);


const TOKEN_KEY = "ez_token";
const USER_KEY = "ez_user";


export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [token, setToken] = useState<string>(readLS<string>(TOKEN_KEY, ""));
    const [user, setUser] = useState<User | null>(readLS<User | null>(USER_KEY, null));
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (token && !user) {
            setLoading(true);
            api.me(token).then((r) => { if (r?.user) { setUser(r.user); writeLS(USER_KEY, r.user); } }).finally(() => setLoading(false));
        }
    }, [token]);

    const login = async (email: string, password: string) => {
        setLoading(true); const r = await api.login({ email, password }); setLoading(false);
        if (r?.ok) { setToken(r.token || "mock-token"); writeLS(TOKEN_KEY, r.token || "mock-token"); setUser(r.user); writeLS(USER_KEY, r.user); return true; }
        return false;
    };

    const register = async (payload: { email: string; password: string; clubName: string; sport: string; league: string }) => {
        setLoading(true); const r = await api.register(payload); setLoading(false); return r;
    };

    const logout = () => { setToken(""); setUser(null); removeLS(TOKEN_KEY); removeLS(USER_KEY); };

    return (
        <Ctx.Provider value={{ token, user, loading, login, register, logout }}>
            {children}
        </Ctx.Provider>
    );
}