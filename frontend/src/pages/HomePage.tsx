import React from "react";
import Shell from "../components/Shell";


export default function HomePage() {
    return (
        <Shell>
            <section className="flex flex-col items-center">
                {/* Main Pitch */}
                <p style={{
                    textAlign: 'center',
                    fontSize: '2em',
                    fontWeight: 600,
                    maxWidth: '900px',
                    margin: '0 auto 20px',
                    lineHeight: 1.4,
                    color: 'white'
                }}>
                    <strong>Still wasting time manually entering your team's schedule into TeamSnap?</strong>
                    <br style={{ marginBottom: '12px' }} />
                    <span style={{ display: 'inline-block', marginTop: '12px' }}>
                        <strong>EZ‑Schedule makes it effortless.</strong>
                    </span>
                </p>

                <div style={{
                    maxWidth: '900px',
                    margin: '0 auto 30px',
                    fontSize: '1.4em',
                    lineHeight: 1.6,
                    textAlign: 'center',
                    color: 'white',
                    fontWeight: 400
                }}>
                    With EZ‑Schedule, your games, matches, and events are automatically synced into TeamSnap—fast, accurate, and hassle-free.
                    Whether it's soccer, hockey, basketball, baseball, or more, our system keeps your schedule updated and ready for your players in seconds.
                    <br /><br />
                    <strong>You focus on the game. We handle the rest.</strong>
                </div>

                {/* Features Section */}
                <div style={{
                    display: 'flex',
                    flexWrap: 'wrap',
                    justifyContent: 'center',
                    gap: '20px',
                    marginTop: 0,
                    fontSize: '1.2em'
                }}>
                    {[
                        { title: "⚽ Multi‑Sport Compatibility", text: "Supports all major sports and league formats with ease." },
                        { title: "🔁 Seamless Automation", text: "Set it up once and watch your schedule update automatically." },
                        { title: "🚀 Quick Integration", text: "Connect to TeamSnap in just minutes—no tech skills required." },
                    ].map((feature) => (
                        <div 
                            key={feature.title} 
                            style={{
                                backgroundColor: '#64BB7E',
                                padding: '25px',
                                borderRadius: '10px',
                                width: '260px',
                                textAlign: 'center'
                            }}
                        >
                            <h3 style={{
                                color: 'white',
                                marginTop: 0,
                                marginBottom: '12px',
                                fontSize: '1.4em'
                            }}>
                                {feature.title}
                            </h3>
                            <p style={{
                                color: 'white',
                                margin: 0
                            }}>
                                {feature.text}
                            </p>
                        </div>
                    ))}
                </div>
            </section>
        </Shell>
    );
}