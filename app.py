from flask import Flask, jsonify
from flask_restful import Api, Resource
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_bcrypt import Bcrypt

import datetime
from sqlalchemy.ext.hybrid import hybrid_property
from flask_bcrypt import generate_password_hash

# CONFIG
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lms.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'faec6b0b19d8ce115edc970d2d38d96c'

db = SQLAlchemy(app)
admin = Admin(app)
api = Api(app)
bcrypt = Bcrypt(app)
mm = Marshmallow(app)


# MODELS
# USERS
class User(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(150))
    email = db.Column(db.String(150))
    _password = db.Column(db.String(350))
    user_type = db.Column(db.String(50))
    full_name = db.Column(db.String(150))
    address = db.Column(db.String(450))
    date = db.Column(db.DateTime, default=datetime.datetime.utcnow())
    added_by = db.Column(db.Integer(), nullable=True)
    book_borrowed = db.Column(db.Text, nullable=True)

    # Relationship
    category = db.relationship('Category', backref='user', lazy=True)
    books = db.relationship('Books', backref='user', lazy=True)

    # USER TYPES
    Admin = 'Admin'
    Librarian = 'Librarian'
    Public = 'Public'

    @hybrid_property
    def password(self):
        return self._password

    @password.setter
    def _set_password(self, plaintext):
        self._password = bcrypt.generate_password_hash(plaintext)

    def __repr__(self):
        return f'{self.username} - {self.user_type}'


# CATEGORY
class Category(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(150))
    date = db.Column(db.DateTime, default=datetime.datetime.utcnow())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    # Relationship
    books = db.relationship('Books', backref='category', lazy=True)

    def __repr__(self):
        return self.name


# BOOKS
class Books(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(500))
    description = db.Column(db.Text)
    count = db.Column(db.Integer)
    date = db.Column(db.DateTime, default=datetime.datetime.utcnow())
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return self.name


# HISTORY
class History(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.datetime.utcnow())
    type = db.Column(db.String(50))


# ADMIN
admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Category, db.session))
admin.add_view(ModelView(Books, db.session))
admin.add_view(ModelView(History, db.session))


# VIEWS
# USER LIST
class UserList(Resource):
    def get(self):
        print('ok')
        data = History.query.all()
        for i in data:
            print(i.user_id)

        return 'ok'


api.add_resource(UserList, '/')


if __name__ == '__main__':
    app.run(debug=True)
