from flask_restful import abort
from .DB.models import db, User, History, TokenBlocklist
from http import HTTPStatus
from app import jwt
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from flask_jwt_extended.exceptions import JWTExtendedException
from jwt import PyJWTError
from functools import wraps
from typing import Dict, Union


# For success response
def success_response(data=None, code=None, msg=None, status=None):
    return dict(code=code, message=msg, data=data, status=status)

# General Auth check
def auth_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
        except (JWTExtendedException, PyJWTError):
            abort(HTTPStatus.UNAUTHORIZED,
                  error='Login required',
                  status='UNAUTHORIZED')

        return fn(*args, **kwargs)

    return wrapper

# Admin Auth check
def admin_access(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
        except (JWTExtendedException, PyJWTError):
            abort(HTTPStatus.UNAUTHORIZED,
                  error='Login Expired',
                  status='UNAUTHORIZED')
        identity = get_jwt_identity()

        if identity['role'] != User.Admin:
            abort(HTTPStatus.FORBIDDEN,
                  error="You don't have the permission to access this",
                  status='FORBIDDEN')
        return fn(*args, **kwargs)

    return wrapper

# Librarian_access Auth check
def librarian_access(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
        except (JWTExtendedException, PyJWTError):
            abort(HTTPStatus.UNAUTHORIZED,
                  error='Login Expired',
                  status='UNAUTHORIZED')
        identity = get_jwt_identity()

        if identity['role'] == User.Public:
            abort(HTTPStatus.FORBIDDEN,
                  error="You don't have the permission to access this",
                  status='FORBIDDEN')

        return fn(*args, **kwargs)

    return wrapper

# Checking Public or not
@librarian_access
def is_public():
    pass

# Checking for JWT token in blocklist
@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload: dict) -> bool:
    jti = jwt_payload["jti"]
    token = db.session.query(TokenBlocklist.id).filter_by(jti=jti).scalar()

    return token is not None

# Common DB summit
def user_summit(data, code=HTTPStatus.OK, msg='Done', check_existing=True):
    try:
        db.session.add(data)
        db.session.commit()
    except Exception as e:
        if check_existing:
            error_field = 'username' if 'user.username' in str(e) else 'email'
            abort(HTTPStatus.CONFLICT,
                  error=f"{error_field} already exists",
                  status='CONFLICT')

    return success_response(code=code,
                            msg=msg,
                            status='OK')

# Category DB summit
def category_summit(data, code, msg):
    try:
        db.session.add(data)
        db.session.commit()

    except Exception as e:
        if 'category.name' in str(e):
            abort(HTTPStatus.CONFLICT,
                  error=f"Category already exits",
                  status='CONFLICT')

    return success_response(code=code,
                            msg=msg,
                            status='OK')

# Book DB summit
def book_summit(data, code, msg):
    try:
        db.session.add(data)
        db.session.commit()

    except Exception as e:
        if 'book.title' in str(e):
            abort(HTTPStatus.CONFLICT,
                  error=f"Book already exits",
                  status='CONFLICT')

    return success_response(code=code,
                            msg=msg,
                            status='OK'), code

# Checking if a user can review a book ot not
def can_review(user_id: str, book_id: str) -> bool:
    history = History.query.filter_by(user_id=user_id, book_id=book_id).first()
    if history:
        return True
    return False

# Initial creation of all Tables & Admin user
def create_db(app) -> None:
    with app.app_context():
        db.create_all()

        admin_user: User = User(username='admin', email='admin@gmail.com', first_name="admin", last_name='',
                                password='1234', user_type=User.Admin)
        user_summit(admin_user, check_existing=False)
