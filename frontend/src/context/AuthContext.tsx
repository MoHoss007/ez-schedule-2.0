import React, { createContext, useContext, useEffect, useState } from "react";
import { api } from "../lib/api";


interface User { id: number; email: string; club?: string; teamsRegistered?: number }
interface AuthCtx {
    user: User | null;
    loading: boolean;
    login: (email: string, password: string) => Promise<boolean>;
    register: (payload: { email: string; password: string; username: string }) => Promise<boolean>;
    logout: () => Promise<void>;
}


const Ctx = createContext<AuthCtx>({} as any);
export const useAuth = () => useContext(Ctx);


// Cookie-based auth; no local token storage
export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);

    // On mount, check authentication status
    useEffect(() => {
        api.me()
            .then((r) => {
                if (r.authenticated) setUser({ id: r.id, email: r.email, club: r.club, teamsRegistered: r.teamsRegistered });
                else setUser(null);
            })
            .finally(() => setLoading(false));
    }, []);

    const login = async (email: string, password: string) => {
        console.log("AuthContext: Starting login process for:", email);
        setLoading(true);
        try {
            console.log("AuthContext: Calling api.login");
            const r = await api.login({ email, password });
            console.log("AuthContext: Login response:", r);
            
            if (!r.ok) {
                console.log("AuthContext: Login failed - no ok field or ok is false");
                return false;
            }
            
            console.log("AuthContext: Login successful, now calling api.me");
            const me = await api.me();
            console.log("AuthContext: Me response:", me);
            
            if (me.authenticated) {
                console.log("AuthContext: User authenticated, setting user state");
                setUser({ id: me.id, email: me.email, club: me.club, teamsRegistered: me.teamsRegistered });
            } else {
                console.log("AuthContext: User not authenticated according to /me endpoint");
            }
            return me.authenticated;
        } catch (error) {
            console.error("AuthContext: Login error:", error);
            return false;
        } finally {
            setLoading(false);
            console.log("AuthContext: Login process completed");
        }
    };

    const register = async (payload: { email: string; password: string; username: string }) => {
        setLoading(true);
        try {
            const r = await api.register(payload);
            if (r.ok) {
                // After successful registration, get user info and set state
                const me = await api.me();
                if (me.authenticated) setUser({ id: me.id, email: me.email, club: me.club, teamsRegistered: me.teamsRegistered });
                return true;
            }
            return false;
        } finally {
            setLoading(false);
        }
    };

    const logout = async () => {
        await api.logout();
        setUser(null);
    };

    return <Ctx.Provider value={{ user, loading, login, register, logout }}>{children}</Ctx.Provider>;
 }