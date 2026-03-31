# config.py

import os


class Config:
   
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'this_is_my_secret_key'

    
    SQLALCHEMY_DATABASE_URI = 'sqlite:///db.sqlite3'

    # This is just to disable a warning (not needed feature)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
