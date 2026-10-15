import os
from dotenv import load_dotenv
load_dotenv()


BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "revy-basma-secret-key-2026")
    # Ensure SQLite paths are absolute so Windows doesn't throw OperationalError
    _db_url = os.getenv("DATABASE_URL")
    if not _db_url:
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'geoattend.db')}"
    elif _db_url.startswith("sqlite:///") and not os.path.isabs(_db_url[10:]) and not (len(_db_url) > 11 and _db_url[11] == ':'):
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, _db_url[10:])}"
    else:
        SQLALCHEMY_DATABASE_URI = _db_url

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Batch 12 — WebAuthn (Relying Party) config. Defaults match local dev
    # (localhost, plain http). Override via env vars for staging/prod — RP_ID
    # must be the bare domain (no scheme/port), ORIGIN must be the exact
    # scheme+host+port the browser sees, or every ceremony will fail.
    WEBAUTHN_RP_ID = os.getenv("WEBAUTHN_RP_ID", "localhost")
    WEBAUTHN_RP_NAME = os.getenv("WEBAUTHN_RP_NAME", "ريفي بصمة")
    WEBAUTHN_ORIGIN = os.getenv("WEBAUTHN_ORIGIN", "http://localhost:5000")

    # CARTO CDN Maps API Key
    CARTO_API_KEY = os.environ.get("CARTO_API_KEY", "")