// src/pages/DashboardPage.tsx
import { useEffect, useState } from "react";
import { Shell } from "../components/Shell";
import { useAuth } from "../context/AuthContext";
import { api } from "../lib/api";
import { useNavigate } from "react-router-dom";

interface Subscription {
  id: number;
  billed_team_count: number;
  team_limit: number;
  league_id: number;
  league_name: string;
  league_season_id: number;
  season_name: string;
  status: string;
  billing_start_at: string;
  created_at: string;
  updated_at: string;
  user_id: number;
}

export default function DashboardPage() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSubs = async () => {
      if (!user?.id) {
        setLoading(false);
        return;
      }
      try {
        setLoading(true);
        setError(null);
        const res = await api.getSubscriptions(user.id);

        // Accept single object, array, or {data: [...]}
        if (Array.isArray(res)) {
          setSubscriptions(res);
        } else if (res && Array.isArray((res as any).data)) {
          setSubscriptions((res as any).data);
        } else if (res && typeof res === "object") {
          setSubscriptions([res as Subscription]);
        } else {
          setSubscriptions([]);
        }
      } catch (err) {
        console.error(err);
        setError("Unable to load subscriptions right now.");
      } finally {
        setLoading(false);
      }
    };

    fetchSubs();
  }, [user?.id]);

  const formatDate = (iso?: string | null) => {
    if (!iso) return "—";
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return "—";
    return d.toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  const clubName =
    (user as any)?.club_name || (user as any)?.club || "Your club";

  const totalSubscriptions = subscriptions.length;
  const totalTeamsBilled = subscriptions.reduce(
    (sum, s) => sum + (s.billed_team_count || 0),
    0
  );
  const totalTeamLimit = subscriptions.reduce(
    (sum, s) => sum + (s.team_limit || 0),
    0
  );

  return (
    <Shell>
      <div className="dash-page">
        {/* Page header */}
        <div className="dash-header">
          <div>
            <h2 className="dash-title">Dashboard</h2>
            <p className="dash-subtitle">
              Overview of your club and subscription usage.
            </p>
          </div>
        </div>

        {/* Two main boxes: Clubs + Subscriptions */}
        <div className="dash-grid-two">
          {/* ========== CLUB BOX ========== */}
          <section className="dash-card">
            <div className="dash-card-header">
              <div>
                <h3 className="dash-card-title">Clubs</h3>
                <p className="dash-card-subtitle">
                  High-level details about your primary club.
                </p>
              </div>
            </div>

            <div className="dash-card-body">
              <div className="dash-club-row">
                <span className="dash-club-label">Primary club</span>
                <span className="dash-club-value">{clubName}</span>
              </div>
              <div className="dash-club-row">
                <span className="dash-club-label">Account owner</span>
                <span className="dash-club-value">{user?.email ?? "—"}</span>
              </div>
              <div className="dash-club-row">
                <span className="dash-club-label">Teams</span>
                <span className="dash-club-value">
                  Coming soon – per-team breakdown.
                </span>
              </div>
              <div className="dash-club-row">
                <span className="dash-club-label">Integrations</span>
                <span className="dash-club-value">
                  TeamSnap (connected) – more integrations coming.
                </span>
              </div>
            </div>

            <div className="dash-card-footer">
              <button
                type="button"
                className="dash-secondary-btn"
                onClick={() =>
                  alert("Club management UI coming soon (placeholder).")
                }
              >
                Manage clubs
              </button>
            </div>
          </section>

          {/* ========== SUBSCRIPTIONS BOX ========== */}
          <section className="dash-card">
            <div className="dash-card-header">
              <div>
                <h3 className="dash-card-title">Subscriptions</h3>
                <p className="dash-card-subtitle">
                  Active EZ-Schedule subscriptions and usage.
                </p>
              </div>
              {loading && <span className="dash-badge">Refreshing…</span>}
            </div>

            <div className="dash-card-body">
              {/* Metrics inside this box */}
              <div className="dash-sub-metrics-grid">
                <div className="dash-sub-metric">
                  <div className="dash-sub-metric-label">Subscriptions</div>
                  <div className="dash-sub-metric-value">
                    {totalSubscriptions || "—"}
                  </div>
                  <div className="dash-sub-metric-foot">
                    Plans attached to this account
                  </div>
                </div>
                <div className="dash-sub-metric">
                  <div className="dash-sub-metric-label">Teams billed</div>
                  <div className="dash-sub-metric-value">
                    {totalTeamsBilled || "0"}
                  </div>
                  <div className="dash-sub-metric-foot">
                    Across all active subscriptions
                  </div>
                </div>
                <div className="dash-sub-metric">
                  <div className="dash-sub-metric-label">Team capacity</div>
                  <div className="dash-sub-metric-value">
                    {totalTeamLimit || "0"}
                  </div>
                  <div className="dash-sub-metric-foot">
                    Max teams for current plans
                  </div>
                </div>
              </div>

              {/* Table */}
              {error && <div className="dash-error">{error}</div>}

              <div className="dash-table-card">
                <table className="dash-table">
                  <thead>
                    <tr>
                      <th>League</th>
                      <th>Season</th>
                      <th>Status</th>
                      <th>Teams billed</th>
                      <th>Team limit</th>
                      <th>Billing start</th>
                      <th>Last updated</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {!loading && subscriptions.length === 0 && (
                      <tr>
                        <td colSpan={8} className="dash-table-empty">
                          No subscriptions found for this account.
                        </td>
                      </tr>
                    )}
                    {subscriptions.map((sub) => (
                      <tr key={sub.id}>
                        <td>{sub.league_name}</td>
                        <td>{sub.season_name}</td>
                        <td>
                          <span
                            className={`dash-status-pill dash-status-${sub.status}`}
                          >
                            {sub.status}
                          </span>
                        </td>
                        <td>{sub.billed_team_count}</td>
                        <td>{sub.team_limit}</td>
                        <td>{formatDate(sub.billing_start_at)}</td>
                        <td>{formatDate(sub.updated_at)}</td>
                        <td>
                          <button
                            type="button"
                            className="dash-action-btn"
                            onClick={() =>
                              alert(
                                `Manage subscription #${sub.id} (coming soon).`
                              )
                            }
                          >
                            Manage
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Footer of subscriptions box */}
            <div className="dash-card-footer dash-card-footer-right">
              <button
                type="button"
                className="dash-primary-btn"
                onClick={() => navigate("/subscriptions")}
              >
                Add subscription
              </button>
            </div>
          </section>
        </div>
      </div>
    </Shell>
  );
}
