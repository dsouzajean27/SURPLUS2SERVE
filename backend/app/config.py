import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: str = os.getenv("DB_PORT", "3306")
    DB_USER: str = os.getenv("DB_USER", "s2s_user")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "s2s_pass123")
    DB_NAME: str = os.getenv("DB_NAME", "surplus2serve")
    # Optional full override (used by the automated tests with SQLite)
    DATABASE_URL_OVERRIDE: str = os.getenv("DATABASE_URL", "")

    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dev-secret-change-me")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "10080"))

    # Anyone can pick "admin" on the sign-up form, so admin sign-up needs this code.
    ADMIN_SIGNUP_CODE: str = os.getenv("ADMIN_SIGNUP_CODE", "S2S-ADMIN-2026")

    CORS_ORIGINS: list = [
        o.strip()
        for o in os.getenv(
            "CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
        ).split(",")
        if o.strip()
    ]

    # External services (OpenStreetMap Nominatim geocoding + OSRM routing)
    NOMINATIM_URL: str = os.getenv("NOMINATIM_URL", "https://nominatim.openstreetmap.org/search")
    OSRM_URL: str = os.getenv("OSRM_URL", "https://router.project-osrm.org/route/v1/driving")
    GEO_USER_AGENT: str = os.getenv("GEO_USER_AGENT", "Surplus2Serve-College-Project/1.0")
    GEO_TIMEOUT: float = float(os.getenv("GEO_TIMEOUT", "6"))

    # Optional email notifications (leave SMTP_HOST empty to disable)
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM: str = os.getenv("SMTP_FROM", "no-reply@surplus2serve.local")

    @property
    def DATABASE_URL(self) -> str:
        if self.DATABASE_URL_OVERRIDE:
            return self.DATABASE_URL_OVERRIDE
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


settings = Settings()
