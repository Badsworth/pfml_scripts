import os

config = {}

config["environment"] = os.environ.get("ENVIRONMENT")
config["db_url"] = os.environ.get("DB_URL")
config["db_name"] = os.environ.get("DB_NAME")
config["db_username"] = os.environ.get("DB_USERNAME")
config["db_password"] = os.environ.get("DB_PASSWORD")
