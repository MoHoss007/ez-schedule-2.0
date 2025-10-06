import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import { PRICE_PER_TEAM, api } from "../lib/api";
import { readLS, writeLS } from "../lib/storage";


interface Team { id: number; name: string }
interface CartState { sport: string; league: string; selectedTeamIds: number[] }
const CART_KEY = "ez_cart_v1";
const defaultCart: CartState = { sport: "", league: "", selectedTeamIds: [] };


interface CartCtx extends CartState {
    teams: Team[];
    setTeams: (t: Team[]) => void;
    setSport: (v: string) => void;
    setLeague: (v: string) => void;
    toggleTeam: (id: number, on: boolean) => void;
    count: number;
    subtotal: number;
    loadTeams: (s: string, l: string) => Promise<void>;
    clear: () => void;
}


const CtxCart = createContext<CartCtx>({} as any);
export const useCart = () => useContext(CtxCart);


export function CartProvider({ children }: { children: React.ReactNode }) {
    const [teams, setTeams] = useState<Team[]>([]);
    const [state, setState] = useState<CartState>(() => readLS<CartState>(CART_KEY, defaultCart));
    const persist = (next: CartState) => { setState(next); writeLS(CART_KEY, next); };


    const setSport = (v: string) => persist({ ...state, sport: v, selectedTeamIds: [] });
    const setLeague = (v: string) => persist({ ...state, league: v, selectedTeamIds: [] });
    const toggleTeam = (id: number, on: boolean) => {
        const selected = on ? Array.from(new Set([...state.selectedTeamIds, id])) : state.selectedTeamIds.filter(x => x !== id);
        persist({ ...state, selectedTeamIds: selected });
    };


    const loadTeams = async (sport: string, league: string) => {
        if (!sport || !league) return; const r = await api.listTeams({ sport, league }); if (r?.ok) setTeams(r.teams);
    };


    useEffect(() => { (async () => { await loadTeams(state.sport, state.league); })(); }, [state.sport, state.league]);
    useEffect(() => { const ids = new Set(teams.map(t => t.id)); const pruned = state.selectedTeamIds.filter(id => ids.has(id)); if (pruned.length !== state.selectedTeamIds.length) persist({ ...state, selectedTeamIds: pruned }); }, [teams.length]);


    const count = state.selectedTeamIds.length;
    const subtotal = useMemo(() => +(count * PRICE_PER_TEAM).toFixed(2), [count]);
    const clear = () => { persist(defaultCart); setTeams([]); };


    return (
        <CtxCart.Provider value={{ ...state, teams, setTeams, setSport, setLeague, toggleTeam, count, subtotal, loadTeams, clear }}>
            {children}
        </CtxCart.Provider>
    );
}