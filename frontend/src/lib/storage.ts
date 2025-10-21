export function readLS<T>(key: string, fallback: T): T {
    try { const raw = localStorage.getItem(key); return raw ? (JSON.parse(raw) as T) : fallback; } catch { return fallback; }
}
export function writeLS<T>(key: string, value: T) { try { localStorage.setItem(key, JSON.stringify(value)); } catch { } }
export function removeLS(key: string) { try { localStorage.removeItem(key); } catch { } }