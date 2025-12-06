import React from "react";
import { NavLink, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "./TopNav.css";

interface ShellProps {
  children: React.ReactNode;
}

export function Shell({ children }: ShellProps) {
  const { user, logout } = useAuth();

  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    "topnav-link" + (isActive ? " topnav-link-active" : "");

  return (
    <div className="app-shell">
      {/* Top navigation */}
      <header className="topnav">
  <div className="topnav-inner">
    <Link to="/" className="topnav-logo">
      EZ-Schedule
    </Link>

    {/* Right-side links */}
    <div className="topnav-right">
      <nav className="topnav-main">
        <NavLink to="/" className={navLinkClass} end>
          Home
        </NavLink>

        {!user && (
          <>
            <NavLink to="/login" className="nav-login-link">
              Log in
            </NavLink>
            <NavLink to="/register" className="nav-signup-btn">
              Get started
            </NavLink>
          </>
        )}

        {user && (
          <>
            <NavLink to="/dashboard" className={navLinkClass}>
              Dashboard
            </NavLink>
            <NavLink to="/subscriptions" className={navLinkClass}>
              Subscriptions
            </NavLink>
            <button onClick={logout} className="topnav-logout-btn">
              Logout
            </button>
          </>
        )}
      </nav>
    </div>
  </div>
</header>


      {/* Main content */}
      <main className="app-main">{children}</main>

      {/* Optional small footer */}
      <footer className="app-footer">
        <span>© {new Date().getFullYear()} EZ-Schedule</span>
      </footer>
    </div>
  );
}
