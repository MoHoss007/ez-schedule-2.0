// frontend/src/pages/HomePage.tsx
import { Link, Navigate } from "react-router-dom";
import { Shell } from "../components/Shell";
import { useAuth } from "../context/AuthContext";

export default function HomePage() {
  const { user, loading } = useAuth();

  // If user is logged in, redirect to dashboard
  if (loading) {
    return null; // or a loading spinner
  }

  if (user) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <Shell>
      <section className="home-wrapper">
        {/* HERO */}
        <div className="home-hero">
          <div className="home-hero-text">
            <p className="home-kicker">
              Built for busy coaches &amp; team managers
            </p>

            <h1 className="home-heading">
              Stop copying schedules into TeamSnap by hand.
            </h1>

            <p className="home-description">
              EZ-Schedule connects your league schedule to TeamSnap and keeps it
              in sync automatically. No more spreadsheets, no more late-night
              copy-paste marathons—just a clean schedule that always matches
              your league site.
            </p>

            <div className="home-cta-row">
              <Link to="/register" className="home-cta-primary">
                Get started in minutes
              </Link>
              <Link to="/subscriptions" className="home-cta-secondary">
                View subscription
              </Link>
            </div>

            <p className="home-footnote">
              Beta access • Works for soccer, hockey, basketball, baseball &amp;
              more.
            </p>
          </div>

          {/* Right side “product panel” */}
          <div className="home-hero-panel">
            <div className="home-panel-card">
              <div className="home-panel-header">
                <span className="home-panel-title">Tonight’s schedule</span>
                <span className="home-panel-pill">Synced to TeamSnap</span>
              </div>

              <ul className="home-panel-list">
                <li>
                  <div className="home-panel-game-main">
                    U12 Elite vs Tigers
                    <span className="home-panel-badge">Final</span>
                  </div>
                  <div className="home-panel-game-meta">
                    7:30pm • Rink 2 • GTHL
                  </div>
                </li>
                <li>
                  <div className="home-panel-game-main">
                    U10 Red vs Wolves
                    <span className="home-panel-badge home-panel-badge-alt">
                      Updated
                    </span>
                  </div>
                  <div className="home-panel-game-meta">
                    6:15pm • Field 3 • YRSL
                  </div>
                </li>
                <li>
                  <div className="home-panel-game-main">
                    U14 Academy Training
                  </div>
                  <div className="home-panel-game-meta">
                    5:00pm • Indoor Dome • Team event
                  </div>
                </li>
              </ul>

              <div className="home-panel-footer">
                <div>
                  <div className="home-panel-stat-label">Teams synced</div>
                  <div className="home-panel-stat-value">12</div>
                </div>
                <div>
                  <div className="home-panel-stat-label">Changes this week</div>
                  <div className="home-panel-stat-value">34</div>
                </div>
                <div>
                  <div className="home-panel-stat-label">Manual updates</div>
                  <div className="home-panel-stat-value home-panel-stat-value-ok">
                    0
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* WHY SECTION */}
        <section className="home-section">
          <h2 className="home-section-title">Why teams use EZ-Schedule</h2>

          <div className="feature-grid">
            {[
              {
                title: "⚽ Multi-sport compatible",
                text: "Supports all major sports and league formats—from house league to elite.",
              },
              {
                title: "🔁 Always in sync",
                text: "We watch your league schedule for changes and push updates straight into TeamSnap.",
              },
              {
                title: "📊 Club-level view",
                text: "See every team, every game, and every change from a single dashboard.",
              },
            ].map((f) => (
              <div key={f.title} className="feature-card">
                <h3>{f.title}</h3>
                <p>{f.text}</p>
              </div>
            ))}
          </div>
        </section>

        {/* HOW IT WORKS */}
        <section className="home-section home-steps">
          <h3 className="home-section-subtitle">How it works</h3>
          <div className="home-steps-grid">
            <div className="home-step-card">
              <div className="home-step-number">1</div>
              <h4>Connect your club</h4>
              <p>
                Create your account, add your club details and choose the sport
                and league you play in.
              </p>
            </div>
            <div className="home-step-card">
              <div className="home-step-number">2</div>
              <h4>Select teams &amp; seasons</h4>
              <p>
                Pick the teams and season you want us to manage—we handle the
                fixtures and changes.
              </p>
            </div>
            <div className="home-step-card">
              <div className="home-step-number">3</div>
              <h4>We keep TeamSnap updated</h4>
              <p>
                Schedules are automatically synced to TeamSnap, so players and
                parents always see the latest info.
              </p>
            </div>
          </div>
        </section>
      </section>
    </Shell>
  );
}
