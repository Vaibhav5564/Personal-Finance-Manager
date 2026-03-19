# config.py

# This file is used to store all the configuration settings
# Keeping it separate makes the project clean and easy to manage later

import os


class Config:
    # Secret key is used for session security (login, forms, etc.)
    # In real projects, this should come from environment variables
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'this_is_my_secret_key'

    # Database configuration (SQLite for now)
    # The database will be created inside the instance folder
    SQLALCHEMY_DATABASE_URI = 'sqlite:///db.sqlite3'

    # This is just to disable a warning (not needed feature)
    SQLALCHEMY_TRACK_MODIFICATIONS = False


# You can create different configs later if needed
# For example: DevelopmentConfig, ProductionConfig, etc.