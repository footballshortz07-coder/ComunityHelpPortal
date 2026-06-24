import os
from urllib.parse import quote_plus


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "community-help-portal-secret")

    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DB = os.getenv("MYSQL_DB", "community_help_portal")

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"mysql+pymysql://{MYSQL_USER}:{quote_plus(MYSQL_PASSWORD)}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
