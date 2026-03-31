from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# global objects
db = SQLAlchemy()
login_manager = LoginManager()


def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static')

    #  CONFIG
    app.config['SECRET_KEY'] = 'this_is_a_secret_key_change_later'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    #  INIT DB
    db.init_app(app)

    #  LOGIN MANAGER SETUP
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'  

    #  IMPORT MODELS
    from .models import User

    #  USER LOADER
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    
    @app.after_request
    def add_header(response):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    #  REGISTER ROUTES
    from .routes import main
    app.register_blueprint(main)

    return app