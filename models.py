import datetime
from app import db


# USERS
class User(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(150))
    username= db.Column(db.String(150))
    email = db.Column(db.String(150))
    password = db.Column(db.String())
    user_type = db.Column(db.String(50))
    created = db.Column(db.DateTime, default=datetime.datetime.utcnow())

    # USER TYPES
    Admin = 'Admin'
    Librarian = 'Librarian'
    Public = 'Public'

    def __repr__(self):
        return f'{self.name} - {self.user_type}'