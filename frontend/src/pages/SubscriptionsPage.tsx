// frontend/src/pages/SubscriptionsPage.tsx
import { useState, useEffect } from "react";
import { Shell } from "../components/Shell";
import { api } from "../lib/api";
import { useAuth } from "../context/AuthContext";

interface League {
  id: number;
  name: string;
}

interface Season {
  id: number;
  name: string;
  year: string;
}

export default function SubscriptionsPage() {
  const { user } = useAuth();
  const [leagues, setLeagues] = useState<League[]>([]);
  const [seasons, setSeasons] = useState<Season[]>([]);
  const [selectedLeague, setSelectedLeague] = useState<string>("");
  const [selectedSeason, setSelectedSeason] = useState<string>("");
  const [numberOfTeams, setNumberOfTeams] = useState<number>(1);
  const [loading, setLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);

  const PRICE_PER_TEAM_PER_SEASON = 200;

  useEffect(() => {
    if (selectedLeague) {
      fetchSeasons(selectedLeague);
    } else {
      setSeasons([]);
      setSelectedSeason("");
    }
  }, [selectedLeague]);

  const fetchLeagues = async () => {
    setLoading(true);
    try {
      const res = await api.getLeagues();
      if (res.ok) setLeagues(res.leagues);
    } catch (e) {
      console.error("Failed to fetch leagues", e);
    } finally {
      setLoading(false);
    }
  };

  const fetchSeasons = async (leagueId: string) => {
    setLoading(true);
    try {
      const res = await api.getSeasons(parseInt(leagueId, 10));
      if (res.ok) setSeasons(res.seasons);
    } catch (e) {
      console.error("Failed to fetch seasons", e);
    } finally {
      setLoading(false);
    }
  };

  const calculateTotal = () =>
    PRICE_PER_TEAM_PER_SEASON * Math.max(1, Number(numberOfTeams) || 1);

  const handleSubscribe = async () => {
    if (!selectedLeague || !selectedSeason || numberOfTeams < 1) {
      alert("Please select a league, season, and at least one team.");
      return;
    }
    if (!user || !user.id) {
      alert("You must be logged in to subscribe.");
      return;
    }

    setLoading(true);
    try {
      const res = await api.createSubscription({
        userId: user.id,
        leagueId: parseInt(selectedLeague, 10),
        seasonId: parseInt(selectedSeason, 10),
        numberOfTeams,
      });

      if (!res.ok) {
        alert(res.error || "Failed to create checkout session.");
      }
    } catch (e) {
      console.error("Subscription failed", e);
      alert("Subscription failed, please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Shell>
      <div className="subs-page">
        <div className="subs-container">
          {/* Hero */}
          <div className="subs-hero">
            <h1 className="subs-title">Join EZ-Schedule today</h1>
            <p className="subs-subtitle">
              Get unlimited, automated schedule syncing for your teams — simple
              pricing, built for busy coaches and managers.
            </p>
          </div>

          {!showForm ? (
            // ---------- PRICING CARD ----------
            <div className="subs-card-wrap">
              <div className="subs-card">

                <div className="subs-card-body">
                  <div className="subs-plan-label">Team Subscription</div>
                  <div className="subs-plan-name">
                    SEASON PLAN
                    <br />
                  </div>

                  <div className="subs-price-block">
                    <div className="subs-price-line">
                      <span className="subs-price">${PRICE_PER_TEAM_PER_SEASON}</span>
                      <span className="subs-price-note">per team</span>
                    </div>
                    <div className="subs-price-caption">per season</div>
                  </div>

                  <ul className="subs-features">
                    <li>Automatic schedule sync to TeamSnap</li>
                    <li>Real-time updates from league schedules</li>
                    <li>Multi-team management dashboard</li>
                    <li>Dedicated support throughout the season</li>
                  </ul>

                  <button
                    className="subs-primary-btn"
                    onClick={() => {
                      setShowForm(true);
                      fetchLeagues();
                    }}
                  >
                    Buy Subscription
                  </button>
                  <div className="subs-footnote">Cancel anytime before season starts.</div>
                </div>
              </div>
            </div>
          ) : (
            // ---------- FORM ----------
            <div className="subs-form-wrap">
              <button
                type="button"
                className="subs-back-link"
                onClick={() => setShowForm(false)}
              >
                ← Back to pricing
              </button>

              <div className="subs-form-card">
                <h2 className="subs-form-title">Complete your subscription</h2>
                <p className="subs-form-subtitle">
                  Choose your league, season, and number of teams for this
                  Premium Season plan.
                </p>

                <div className="subs-form-grid">
                  {/* League */}
                  <div className="subs-form-field">
                    <label htmlFor="league" className="subs-label">
                      League
                    </label>
                    <select
                      id="league"
                      value={selectedLeague}
                      onChange={(e) => setSelectedLeague(e.target.value)}
                      disabled={loading}
                      className="subs-input"
                    >
                      <option value="">Choose a league...</option>
                      {leagues.map((l) => (
                        <option key={l.id} value={l.id}>
                          {l.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Season */}
                  <div className="subs-form-field">
                    <label htmlFor="season" className="subs-label">
                      Season
                    </label>
                    <select
                      id="season"
                      value={selectedSeason}
                      onChange={(e) => setSelectedSeason(e.target.value)}
                      disabled={!selectedLeague || loading}
                      className="subs-input"
                    >
                      <option value="">Choose a season...</option>
                      {seasons.map((s) => (
                        <option key={s.id} value={s.id}>
                          {s.name} ({s.year})
                        </option>
                      ))}
                    </select>
                    {!selectedLeague && (
                      <div className="subs-help-text">
                        Please select a league first.
                      </div>
                    )}
                  </div>

                  {/* Teams */}
                  <div className="subs-form-field">
                    <label htmlFor="teams" className="subs-label">
                      Number of teams
                    </label>
                    <input
                      id="teams"
                      type="number"
                      min={1}
                      max={50}
                      value={numberOfTeams}
                      onChange={(e) =>
                        setNumberOfTeams(
                          Math.max(1, parseInt(e.target.value || "1", 10))
                        )
                      }
                      className="subs-input"
                    />
                    <div className="subs-help-text">
                      How many teams do you want to register?
                    </div>
                  </div>

                  {/* Summary */}
                  {numberOfTeams > 0 &&
                    selectedLeague &&
                    selectedSeason && (
                      <div className="subs-summary">
                        <div className="subs-summary-row">
                          <span>
                            {numberOfTeams}{" "}
                            {numberOfTeams === 1 ? "team" : "teams"} × $
                            {PRICE_PER_TEAM_PER_SEASON}
                          </span>
                          <span>
                            ${numberOfTeams * PRICE_PER_TEAM_PER_SEASON}
                          </span>
                        </div>
                        <div className="subs-summary-row subs-summary-total">
                          <span>Total</span>
                          <span>${calculateTotal()}</span>
                        </div>
                        <div className="subs-summary-caption">
                          Billed per season.
                        </div>
                      </div>
                    )}
                </div>

                <button
                  className="subs-primary-btn subs-primary-btn-full"
                  onClick={handleSubscribe}
                  disabled={
                    !selectedLeague ||
                    !selectedSeason ||
                    numberOfTeams < 1 ||
                    loading
                  }
                >
                  {loading
                    ? "Processing…"
                    : `Subscribe ${numberOfTeams} team${
                        numberOfTeams !== 1 ? "s" : ""
                      }`}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </Shell>
  );
}
