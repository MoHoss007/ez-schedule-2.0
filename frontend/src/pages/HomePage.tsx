import React from "react";
import Shell from "../components/Shell";

export default function HomePage() {
  return (
    <Shell>
      <section className="home-wrapper">
        <div className="home-content">
          <h1 className="home-heading">
            Still wasting time manually entering your team’s schedule into
            TeamSnap?
          </h1>

          <h2 className="home-subheading">EZ-Schedule makes it effortless.</h2>

          <p className="home-description">
            With EZ-Schedule, your games, matches, and events are automatically
            synced into TeamSnap—fast, accurate, and hassle-free. Whether it’s
            soccer, hockey, basketball, baseball, or more, our system keeps your
            schedule updated and ready for your players in seconds.
            <br />
            <br />
            <strong>You focus on the game. We handle the rest.</strong>
          </p>

          <div className="feature-grid">
            {[
              {
                title: "⚽ Multi-Sport Compatibility",
                text: "Supports all major sports and league formats with ease.",
              },
              {
                title: "🔁 Seamless Automation",
                text: "Set it up once and watch your schedule update automatically.",
              },
              {
                title: "🚀 Quick Integration",
                text: "Connect to TeamSnap in just minutes—no tech skills required.",
              },
            ].map((f) => (
              <div key={f.title} className="feature-card">
                <h3>{f.title}</h3>
                <p>{f.text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </Shell>
  );
}
