import React, { useState } from "react";
import { Link, useLocation } from "react-router-dom";


export default function Shell({ children }: { children: React.ReactNode }) {
    const [isMenuOpen, setIsMenuOpen] = useState(false);
    const location = useLocation();

    const menuItems = [
        { path: "/", label: "Home", icon: "🏠" },
        { path: "/register", label: "Register", icon: "👤" },
        { path: "/login", label: "Login", icon: "🔑" },
        { path: "/dashboard", label: "Dashboard", icon: "📊" },
        { path: "/register-team", label: "Register Team", icon: "⚽" },
        { path: "/checkout", label: "Checkout", icon: "🛒" },
        { path: "/payment", label: "Payment", icon: "💳" }
    ];

    return (
        <div className="min-h-screen text-white" style={{ 
            background: 'linear-gradient(135deg, #2D3E50 0%, #1E3A8A 100%)' 
        }}>
            <header className="sticky top-0 z-20 border-b-2 border-white/20 bg-black/30 backdrop-blur-md shadow-2xl">
                <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
                    <Link to="/" className="text-3xl font-bold text-white hover:text-[#64BB7E] transition-colors drop-shadow-lg">
                        EZ‑Schedule
                    </Link>
                    
                    {/* Desktop Menu */}
                    <div className="hidden md:block">
                        <div className="bg-gradient-to-r from-gray-800/80 to-gray-700/80 border-2 border-gray-400/60 rounded-2xl p-1 shadow-2xl backdrop-blur-sm">
                            <nav className="flex items-center gap-1">
                                {menuItems.map((item) => (
                                    <Link
                                        key={item.path}
                                        to={item.path}
                                        className={`flex items-center gap-2 px-5 py-3 rounded-xl text-sm font-semibold transition-all duration-200 border-2 ${
                                            location.pathname === item.path
                                                ? "bg-[#64BB7E] text-white shadow-xl border-[#64BB7E] transform scale-105"
                                                : "text-white/95 hover:bg-white/15 hover:text-[#64BB7E] border-transparent hover:border-gray-300/40 hover:shadow-lg hover:transform hover:scale-102"
                                        }`}
                                        style={{
                                            textShadow: location.pathname === item.path ? '0 1px 2px rgba(0,0,0,0.5)' : 'none'
                                        }}
                                    >
                                        <span className="text-lg drop-shadow-sm">{item.icon}</span>
                                        <span className="font-medium">{item.label}</span>
                                    </Link>
                                ))}
                            </nav>
                        </div>
                    </div>

                    {/* Mobile Menu Button */}
                    <button
                        onClick={() => setIsMenuOpen(!isMenuOpen)}
                        className="md:hidden flex items-center justify-center w-14 h-14 rounded-xl bg-gradient-to-b from-gray-700/80 to-gray-800/80 hover:from-gray-600/80 hover:to-gray-700/80 transition-all duration-200 border-2 border-gray-400/60 shadow-xl hover:shadow-2xl hover:scale-105"
                    >
                        <span className="text-2xl text-white drop-shadow-lg">{isMenuOpen ? "✕" : "☰"}</span>
                    </button>
                </div>

                {/* Mobile Menu */}
                {isMenuOpen && (
                    <div className="md:hidden bg-black/50 backdrop-blur-lg border-t-2 border-white/30">
                        <div className="mx-4 mb-6 mt-6">
                            <div className="bg-gradient-to-b from-gray-800/90 to-gray-900/90 border-2 border-gray-400/60 rounded-2xl p-4 shadow-2xl backdrop-blur-sm">
                                <nav className="space-y-3">
                                    {menuItems.map((item) => (
                                        <Link
                                            key={item.path}
                                            to={item.path}
                                            onClick={() => setIsMenuOpen(false)}
                                            className={`flex items-center gap-4 px-5 py-4 rounded-xl text-base font-semibold transition-all duration-200 border-2 ${
                                                location.pathname === item.path
                                                    ? "bg-[#64BB7E] text-white shadow-xl border-[#64BB7E] transform scale-105"
                                                    : "text-white/95 hover:bg-white/15 hover:text-[#64BB7E] border-transparent hover:border-gray-300/40 hover:shadow-lg hover:transform hover:scale-102"
                                            }`}
                                            style={{
                                                textShadow: location.pathname === item.path ? '0 1px 2px rgba(0,0,0,0.5)' : 'none'
                                            }}
                                        >
                                            <span className="text-xl drop-shadow-sm">{item.icon}</span>
                                            <span className="font-medium">{item.label}</span>
                                        </Link>
                                    ))}
                                </nav>
                            </div>
                        </div>
                    </div>
                )}
            </header>
            <main className="mx-auto max-w-6xl px-4 py-8">{children}</main>
            <footer className="border-t border-white/10 py-6 text-center text-xs text-white/70">© {new Date().getFullYear()} EZ‑Schedule</footer>
        </div>
    );
}