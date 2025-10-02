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
    DB_URI = os.getenv("DATABASE_URL", "sqlite:///./test.db")
    POST_AUTH_REDIRECT = os.getenv("POST_AUTH_REDIRECT", "http://localhost:3000")
    API_PREFIX = os.getenv("API_PREFIX", "/api/v1")
