import React from "react";
import { NavLink, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "./TopNav.css"; // we'll add this next

export default function Shell({ children }: { children: React.ReactNode }) {
    const { user, logout } = useAuth();

    return (
        <div className="page-wrap">
            <header className="topbar">
                <div className="container">
                    <Link to="/" className="brand">EZ-Schedule</Link>

                    <nav className="tabs">
                        <NavLink to="/" end className={({ isActive }) => isActive ? "tab active" : "tab"}>Home</NavLink>
                        <NavLink to="/register" className={({ isActive }) => isActive ? "tab active" : "tab"}>Register</NavLink>
                        <NavLink to="/login" className={({ isActive }) => isActive ? "tab active" : "tab"}>Login</NavLink>
                        <NavLink to="/dashboard" className={({ isActive }) => isActive ? "tab active" : "tab"}>Dashboard</NavLink>
                        <NavLink to="/register-team" className={({ isActive }) => isActive ? "tab active" : "tab"}>Register Team</NavLink>
                        <NavLink to="/checkout" className={({ isActive }) => isActive ? "tab active" : "tab"}>Checkout</NavLink>
                        <NavLink to="/payment" className={({ isActive }) => isActive ? "tab active" : "tab"}>Payment</NavLink>
                    </nav>

                    <div className="right">
                        {user ? (
                            <>
                                <div className="who">
                                    <div className="club">{user.club}</div>
                                    <div className="email">{user.email}</div>
                                </div>
                                <button className="btn" onClick={logout}>Logout</button>
                            </>
                        ) : (
                            <div className="who who--anon">Not signed in</div>
                        )}
                    </div>
                </div>
            </header>

            {/* keep your gradient/background for the page body */}
      // ...
            <main className="content">
                <div className="content-inner">
                    {/* NEW: global centering wrapper so all pages are centered */}
                    <div className="center-all">
                        {children}
                    </div>
                </div>
            </main>
            {/* ... */}


            <footer className="footer">© {new Date().getFullYear()} EZ-Schedule</footer>
        </div>
    );
}
