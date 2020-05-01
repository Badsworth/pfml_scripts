import os

from massgov.pfml.util.strings import split_str

config = {}

config["environment"] = os.environ.get("ENVIRONMENT")
config["port"] = os.environ.get("PORT", 1550)
config["db_url"] = os.environ.get("DB_URL")
config["db_name"] = os.environ.get("DB_NAME")
config["db_username"] = os.environ.get("DB_USERNAME")
config["db_password"] = os.environ.get("DB_PASSWORD")
config["db_schema"] = os.environ.get("DB_SCHEMA", "public")
config["cors_origins"] = split_str(os.environ.get("CORS_ORIGINS"))
