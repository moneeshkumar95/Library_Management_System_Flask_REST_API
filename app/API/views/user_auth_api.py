from flask import request, abort
from flask_jwt_extended import get_jwt_identity
from app import Resource, bcrypt
from app.DB.models import User, UserCurrentJWTToken, TokenBlocklist, db
from app.utils import auth_required, librarian_access, user_summit, success_response
from flask_jwt_extended import get_jti, get_jwt, create_access_token
from http import HTTPStatus
import datetime


class UserRegisterAPI(Resource):
    """"
    POST
    """

    @librarian_access
    def post(self):
        """
        API for the user creation

        :return: User data with access token
        """
        request_data = request.json

        try:
            username = request_data.get('username').lower().strip()
            email = request_data.get('email').lower().strip()
            first_name = request_data.get('first_name').lower().strip()
            last_name = request_data.get('last_name').lower().strip()
            full_name = f"{first_name} {last_name}"
            address = request_data.get('address').lower().strip()
            phone = request_data.get('phone').lower().strip()
            password1 = request_data.get('password1').strip()
            password2 = request_data.get('password2').strip()

            if password1 != password2:
                abort(HTTPStatus.CONFLICT,
                      error="Password and Conform password doesn't match, Please try again",
                      status='CONFLICT')

            identity = get_jwt_identity()
            current_user = User.get_by_id(identity['id'])

            user_type = request_data.get('user_type') if current_user.user_type == User.Admin else User.Public
            created_user = User(username=username, email=email, first_name=first_name, last_name=last_name,
                                full_name=full_name, password=password1, phone=phone, address=address,
                                user_type=user_type, activated_by=current_user)

            return user_summit(data=created_user, code=HTTPStatus.CREATED, msg="User created successfully")
        except AttributeError:
            abort(HTTPStatus.BAD_REQUEST,
                  error="Please provide all the data",
                  status='BAD_REQUEST')


class UserAuthenticationAPI(Resource):
    """"
    POST
    """

    def post(self):
        """
        API for the user authentication by username or email

        :return: User data with access token
        """
        request_data = request.json
        if not request_data:
            abort(HTTPStatus.NOT_ACCEPTABLE,
                  error='JSON data missing',
                  status='NOT_ACCEPTABLE')

        username_email = request_data.get('user', '')
        password = request_data.get('password', '')

        if '@' in username_email:
            user = User.query.filter_by(email=username_email).first()
        else:
            user = User.query.filter_by(username=username_email).first()

        if not user:
            abort(HTTPStatus.NOT_FOUND,
                  error='User not found',
                  status='NOT_FOUND')

        if not user.is_active:
            abort(HTTPStatus.FORBIDDEN,
                  error='Your account is deactivated, Please contact library',
                  status='NOT_FOUND')

        if not bcrypt.check_password_hash(user.password_hash, password):
            abort(HTTPStatus.FORBIDDEN,
                  error="Invalid password",
                  status='FORBIDDEN')

        access_token = create_access_token(identity={"id": user.id,
                                                     "role": user.user_type,
                                                     'active': user.is_active})

        user_token = UserCurrentJWTToken.query.filter_by(user_id=user.id).first()

        if user_token:
            user_token.jti = get_jti(access_token)
        else:
            user_token = UserCurrentJWTToken(user_id=user.id, jti=get_jti(access_token))

        db.session.add(user_token)
        db.session.commit()

        user = {'user_id': user.id,
                'name': user.full_name,
                'role': user.user_type,
                'access_token': access_token}

        return success_response(code=HTTPStatus.OK,
                                data=user,
                                msg='Successfully logged-in',
                                status='OK')


class LogoutAPI(Resource):
    """"
    DELETE
    """

    @auth_required
    def delete(self):
        """
        API for adding logged out jwt tokens in blocklist
        :return: Success code in JSON response
        """
        jti = get_jwt().get('jti', '')
        blocklist = TokenBlocklist(jti=jti)
        db.session.add(blocklist)
        db.session.commit()

        return success_response(code=HTTPStatus.OK,
                                msg='Logged out Successfully',
                                status='OK')


class PasswordChange(Resource):
    """
    PUT
    """

    @auth_required
    def put(self):
        """
        API for user password change

        :return: Success or error response
        """
        identity = get_jwt_identity()
        user = User.get_by_id(identity['id'])

        request_data = request.json

        try:
            current_password = request_data.get('current_password').strip()
            new_password1 = request_data.get('new_password1').strip()
            new_password2 = request_data.get('new_password2').strip()

            if not user.verify_password(current_password):
                abort(HTTPStatus.FORBIDDEN,
                      error="Invalid password",
                      status='FORBIDDEN')
            if new_password1 != new_password2:
                abort(HTTPStatus.CONFLICT,
                      error="Password and Conform password doesn't match, Please try again",
                      status='CONFLICT')

            user.password = new_password1
            db.session.commit()

            return success_response(code=HTTPStatus.OK,
                                    msg='Password changed successfully',
                                    status='OK')
        except AttributeError:
            abort(HTTPStatus.BAD_REQUEST,
                  error="Please provide all the data",
                  status='BAD_REQUEST')


class UserActivationAPI(Resource):
    """"
    PUT
    """

    @librarian_access
    def put(self, _id):
        """
        API for user activation

        :param : User ID
        :return: Success or error response
        """
        request_data = request.json
        identity = get_jwt_identity()
        current_user = User.get_by_id(identity['id'])
        user = User.get_by_id(_id)
        is_active = request_data.get('is_active', user.is_active)

        if not ((current_user.user_type == User.Librarian and user.user_type == User.Public) or
                current_user.user_type == User.Admin):
            abort(HTTPStatus.FORBIDDEN,
                  error="You don't have the permission to access this",
                  status='FORBIDDEN')

        user.is_active = is_active
        user.activated_by = current_user
        user.updated_by = repr(current_user)
        user.updated_at = datetime.datetime.utcnow()
        db.session.commit()

        return user_summit(code=HTTPStatus.OK,
                           data=user,
                           msg='User updated successfully')
