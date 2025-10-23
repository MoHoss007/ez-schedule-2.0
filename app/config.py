import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev")
    # TeamSnap OAuth settings
    TEAMSNP_AUTH_BASE = os.getenv(
        "TEAMSNP_AUTH_BASE", "https://auth.teamsnap.com"
    ).rstrip("/")
    TEAMSNP_CLIENT_ID = os.getenv("TEAMSNP_CLIENT_ID", "")
    TEAMSNP_CLIENT_SECRET = os.getenv("TEAMSNP_CLIENT_SECRET", "")
    TEAMSNP_REDIRECT_URI = os.getenv(
        "TEAMSNP_REDIRECT_URI", "urn:ietf:wg:oauth:2.0:oob"
    )
    TEAMSNP_SCOPES = os.getenv("TEAMSNP_SCOPES", "read write")
    # Database settings
    DB_URI = os.getenv("EZ_SCHEDULE_DB_URI", "sqlite:///./test.db")
    POST_AUTH_REDIRECT = os.getenv("POST_AUTH_REDIRECT", "http://localhost:3000")
    API_PREFIX = os.getenv("API_PREFIX", "/api/v1")

    # JWT settings
    JWT_SECRET = os.getenv("JWT_SECRET", "dev")
    JWT_ACCESS_TTL_MIN = int(os.getenv("JWT_ACCESS_TTL_MIN", "15"))
    JWT_REFRESH_TTL_DAYS = int(os.getenv("JWT_REFRESH_TTL_DAYS", "30"))

    # Cookie settings
    COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"
    COOKIE_DOMAIN = os.getenv("COOKIE_DOMAIN", None)  # None for localhost
    COOKIE_SAMESITE = os.getenv("COOKIE_SAMESITE", "None")  # Lax, Strict, None

    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
