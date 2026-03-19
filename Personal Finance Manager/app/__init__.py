from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# creating objects here so we can use them in other files easily
db = SQLAlchemy()
login_manager = LoginManager()


def create_app():
    # creating the main flask app
    app = Flask(__name__, template_folder='../templates', static_folder='../static')

    # basic configuration
    app.config['SECRET_KEY'] = 'this_is_a_secret_key_change_later'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # initializing database with app
    db.init_app(app)

    # setting up login manager
    login_manager.init_app(app)
    login_manager.login_view = 'login'  # if user not logged in → redirect here

    # importing models so tables can be created
    from .models import User

    # this function tells flask-login how to load a user
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # importing routes and registering them
    from .routes import main
    app.register_blueprint(main)

    return app