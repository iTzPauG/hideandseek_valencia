import os

PROJECT_ID = os.getenv("GCP_PROJECT_ID", "hidenseekpau")
DATABASE_URL = os.getenv("DATABASE_URL", "")  # postgresql+asyncpg://user:pass@/db?host=/cloudsql/...
SECRET_KEY = os.getenv("SECRET_KEY", "changeme")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days
