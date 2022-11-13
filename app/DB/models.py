from app import db, bcrypt
from flask_restful import abort
from http import HTTPStatus
import uuid
import datetime

# For generating UUID
generate_id = lambda: str(uuid.uuid4())


# User Model
class User(db.Model):
    __tablename__ = "user"
    # USER TYPES
    Admin = 'Admin'
    Librarian = 'Librarian'
    Public = 'Public'

    id = db.Column(db.String(40), primary_key=True, unique=True, default=generate_id)
    username = db.Column(db.String(150), primary_key=True, unique=True, index=True)
    email = db.Column(db.String(150), primary_key=True, unique=True, index=True)
    phone = db.Column(db.String(20), index=True)
    password_hash = db.Column(db.String(500))
    user_type = db.Column(db.String(15), index=True)
    first_name = db.Column(db.String(150))
    last_name = db.Column(db.String(150))
    full_name = db.Column(db.String(300), index=True)
    address = db.Column(db.String(450))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_by = db.Column(db.String(250), nullable=True)
    book_borrowed = db.Column(db.Text, nullable=True, default='[]')

    # Foreign Key
    activated_user_id = db.Column(db.String(40), db.ForeignKey('user.id'), nullable=True)

    # Relationship
    activated_by = db.relationship('User', backref='activated_users_by_me', lazy=True, remote_side=id)
    added_categories = db.relationship('Category', backref='added_by', lazy=True)
    added_books = db.relationship('Book', backref='added_by', lazy=True)
    review = db.relationship('BookReview', backref='user', lazy=True)

    @property
    def password(self):
        return 'Password is not readable'

    @password.setter
    def password(self, pwd):
        self.password_hash = bcrypt.generate_password_hash(pwd).decode('utf8')

    def verify_password(self, pwd):
        return bcrypt.check_password_hash(self.password_hash, pwd)

    def review_book_ids(self):
        return dict(map(lambda x: (x.book_id, x), self.review))

    @staticmethod
    def get_by_id(_id):
        user = User.query.filter_by(id=_id).first()

        if not user:
            abort(HTTPStatus.NOT_FOUND, code=HTTPStatus.NOT_FOUND, error='User not found', staus='NOT_FOUND')

        return user

    def __repr__(self):
        return f'{self.first_name.title()} - {self.user_type}'


category_book = db.Table('category_book',
                         db.Column('category_id', db.String(40), db.ForeignKey('category.id')),
                         db.Column('book_id', db.String(40), db.ForeignKey('book.id')))


# Category Model
class Category(db.Model):
    __tablename__ = "category"
    id = db.Column(db.String(40), primary_key=True, unique=True, default=generate_id)
    name = db.Column(db.String(50), unique=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_by = db.Column(db.String(250), nullable=True)
    user_id = db.Column(db.String(40), db.ForeignKey('user.id'))

    # Relationship
    books = db.relationship('Book', secondary=category_book, backref='category', lazy=True)

    @staticmethod
    def get_by_id(_id):
        category = Category.query.filter_by(id=_id).first()

        if not category:
            abort(HTTPStatus.NOT_FOUND, code=HTTPStatus.NOT_FOUND, error='Category not found', staus='NOT_FOUND')

        return category

    def __repr__(self):
        return self.name


# Book Model
class Book(db.Model):
    __tablename__ = "book"
    id = db.Column(db.String(40), primary_key=True, unique=True, default=generate_id)
    title = db.Column(db.String(650), unique=True, index=True)
    author = db.Column(db.String(150), index=True)
    short_description = db.Column(db.String(650))
    full_description = db.Column(db.Text)
    count = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_by = db.Column(db.String(250), nullable=True)
    overall_rating = db.Column(db.Float, default=0, index=True)
    total_rating = db.Column(db.Integer, default=0)
    total_review = db.Column(db.Integer, default=0)
    user_id = db.Column(db.String(40), db.ForeignKey('user.id'))

    # Relationship
    review = db.relationship('BookReview', backref='book', lazy=True)

    @staticmethod
    def get_by_id(_id):
        book = Book.query.filter_by(id=_id).first()

        if not book:
            abort(HTTPStatus.NOT_FOUND, code=HTTPStatus.NOT_FOUND, error='Book not found', staus='NOT_FOUND')

        return book

    def __repr__(self):
        return self.title


# Book Review Model
class BookReview(db.Model):
    __tablename__ = "book_review"
    id = db.Column(db.String(40), primary_key=True, unique=True, default=generate_id)
    rating = db.Column(db.Integer, index=True)
    review = db.Column(db.String(650))
    create_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    # ForeignKey
    book_id = db.Column(db.String(40), db.ForeignKey('book.id'))
    user_id = db.Column(db.String(40), db.ForeignKey('user.id'))

    @staticmethod
    def get_by_id(_id):
        book_review = BookReview.query.filter_by(id=_id).first()

        if not book_review:
            abort(HTTPStatus.NOT_FOUND, code=HTTPStatus.NOT_FOUND, error='Review not found', staus='NOT_FOUND')

        return book_review

    @staticmethod
    def get_by_book_id(_id):
        book_review = BookReview.query.filter_by(book_id=_id).first()

        if not book_review:
            abort(HTTPStatus.NOT_FOUND, code=HTTPStatus.NOT_FOUND, error='Review not found', staus='NOT_FOUND')

        return book_review

    @staticmethod
    def get_by_user_id(_id):
        book_review = BookReview.query.filter_by(user_id=_id).first()

        if not book_review:
            abort(HTTPStatus.NOT_FOUND, code=HTTPStatus.NOT_FOUND, error='Review not found', staus='NOT_FOUND')

        return book_review

    def __repr__(self):
        return str(self.rating)


# History Model
class History(db.Model):
    __tablename__ = "history"
    borrow_book = 'Borrow'
    return_book = 'Return'

    id = db.Column(db.String(40), primary_key=True, unique=True, default=generate_id)
    user_id = db.Column(db.String(40), primary_key=True)
    book_id = db.Column(db.String(40), primary_key=True)
    book_title = db.Column(db.String(650), index=True)
    user_name = db.Column(db.String(650), index=True)
    date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    type = db.Column(db.String(10), index=True)

    @staticmethod
    def get_by_book_id(_id):
        history = History.query.filter_by(book_id=_id).first()

        if not history:
            abort(HTTPStatus.NOT_FOUND, code=HTTPStatus.NOT_FOUND, error='History not found', staus='NOT_FOUND')

        return history

    @staticmethod
    def get_by_user_id(_id):
        history = History.query.filter_by(user_id=_id).first()

        if not history:
            abort(HTTPStatus.NOT_FOUND, code=HTTPStatus.NOT_FOUND, error='History not found', staus='NOT_FOUND')

        return history

    def __repr__(self):
        return self.id


# For tracking current user JWT Token Model
class UserCurrentJWTToken(db.Model):
    __tablename__ = "user_current_jwt_token"
    user_id = db.Column(db.String(40), primary_key=True, unique=True)
    jti = db.Column(db.String(40))

    def __repr__(self):
        return self.jti

# Token Blocklist Model
class TokenBlocklist(db.Model):
    id = db.Column(db.String(40), primary_key=True, unique=True, default=generate_id)
    jti = db.Column(db.String(40), nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)

    def __repr__(self):
        return self.jti
