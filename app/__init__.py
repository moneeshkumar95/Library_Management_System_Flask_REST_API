from flask import Flask, Blueprint
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
import datetime


db = SQLAlchemy()
bp_api = Blueprint('api', __name__, url_prefix='/api')
api = Api(bp_api)
jwt = JWTManager()
bcrypt = Bcrypt()
mm = Marshmallow()


def create_app() -> Flask:
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lms.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'faec6b0b19d8ce115edc970d2d38d96c'
    app.config['JWT_SECRET_KEY'] = 'niec6b0b19d8ce115edc970d2d38d96m'
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(days=1)

    db.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)
    mm.init_app(app)


    from .utils import create_db
    create_db(app)

    from .API.urls import bp_user_auth, bp_user, bp_category, bp_book
    app.register_blueprint(bp_user_auth)
    app.register_blueprint(bp_user)
    app.register_blueprint(bp_category)
    app.register_blueprint(bp_book)
    app.register_blueprint(bp_api)

    print("-------App created Successfully-------")
    print("-------Tables created Successfully-------")
    print("-------Admin created Successfully-------")
    return app
