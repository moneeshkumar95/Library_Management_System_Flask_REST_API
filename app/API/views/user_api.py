from flask import request, abort
from flask_jwt_extended import get_jwt_identity
from flask_restful import Resource
from app.DB.models import User, UserCurrentJWTToken, TokenBlocklist, db
from app.DB.serializers import UserSerializer
from app.utils import auth_required, librarian_access, user_summit, success_response
from http import HTTPStatus
import datetime


class UserListAPI(Resource):
    """"
    GET
    """

    @librarian_access
    def get(self):
        """
        API for list tha all users

        :return: Users data
        """
        req_args = request.args.to_dict()
        page_num = int(req_args.get("page_num", 1))
        per_page = int(req_args.get("per_page", 10))
        identity = get_jwt_identity()
        req_args.pop('page_num', None)
        req_args.pop('per_page', None)
        filters = [User.id.isnot(None)]

        filter_mapper = {"user_type": User.user_type.in_(req_args.get("user_type", "").split(",")),
                         "email": User.email == req_args.get("email", ""),
                         "username": User.username.contains(req_args.get("username", "")),
                         "full_name": User.full_name.contains(req_args.get("full_name", "")),
                         "is_active": User.is_active.in_(req_args.get("is_active", "").split(","))}

        if identity['role'] == User.Librarian:
            req_args.pop("user_type", None)
            filters[0] = User.user_type == User.Public

        for req_arg in req_args:
            filters[0] = filters[0] & filter_mapper.get(req_arg)

        users = User.query.filter(*filters).order_by(User.username).paginate(page=page_num,
                                                                             per_page=per_page,
                                                                             error_out=False)

        serializer = UserSerializer(only=('id', 'full_name', 'username', 'email', 'is_active', 'user_type'),
                                    many=True)
        data = serializer.dump(users.items)

        return dict(code=HTTPStatus.OK,
                    data=data,
                    msg='Successfully retrieved users',
                    status='OK',
                    previous=users.prev_num,
                    next=users.next_num,
                    total=users.total)


class UserAPI(Resource):
    """"
    GET, PUT, DELETE
    """

    @auth_required
    def get(self, _id):
        """
        API for detailed user

        :param :  User ID
        :return: User data
        """
        user = User.get_by_id(_id)
        identity = get_jwt_identity()
        current_user = User.get_by_id(identity['id'])
        current_user_type = current_user.user_type

        if not ((current_user_type == User.Librarian and user.user_type == User.Public) or
                ((
                         current_user_type == User.Librarian or current_user_type == User.Public) and current_user.id == _id) or
                current_user_type == User.Admin):
            abort(HTTPStatus.FORBIDDEN,
                  error="You don't have the permission to access this",
                  status='FORBIDDEN')

        serializer = UserSerializer()
        data = serializer.dump(user)

        return success_response(code=HTTPStatus.OK,
                                data=data,
                                msg='User data retrieved successfully',
                                status='OK')

    @auth_required
    def put(self, _id):
        """
        API for update user data

        :param :  User ID
        :return: Success or error response
        """
        request_data = request.json
        user = User.get_by_id(_id)
        identity = get_jwt_identity()
        current_user = User.get_by_id(identity['id'])
        current_user_type = current_user.user_type

        if not ((current_user_type == User.Librarian and user.user_type == User.Public) or
                ((
                         current_user_type == User.Librarian or current_user_type == User.Public) and current_user.id == _id) or
                current_user_type == User.Admin):
            abort(HTTPStatus.FORBIDDEN,
                  error="You don't have the permission to access this",
                  status='FORBIDDEN')

        if current_user_type == User.Admin:
            user.user_type = request_data.get('user_type', current_user_type)
            user.email = request_data.get('email', user.email).lower().strip()
            user.username = request_data.get('username', user.username).lower().strip()

        if 'is_active' in request_data and ((
                                                    current_user.user_type == User.Librarian and user.user_type == User.Public) or current_user.user_type == User.Admin):
            user.is_active = request_data.get('is_active', user.is_active)
            user.activated_by = current_user

        user.first_name = request_data.get('first_name', user.first_name).lower().strip()
        user.last_name = request_data.get('last_name', user.last_name).lower().strip()
        user.address = request_data.get('address', user.address).lower().strip()
        user.phone = request_data.get('phone', user.phone).lower().strip()
        user.updated_by = repr(current_user)
        user.updated_at = datetime.datetime.utcnow()
        db.session.commit()

        return user_summit(code=HTTPStatus.OK,
                           data=user,
                           msg='User data updated successfully')

    @librarian_access
    def delete(self, _id):
        """
        API for delete user

        :param :  User ID
        :return: Success or error response
        """
        user = User.get_by_id(_id)
        identity = get_jwt_identity()
        current_user = User.get_by_id(identity['id'])

        if not ((
                        current_user.user_type == User.Librarian and user.user_type == User.Public) or current_user.user_type == User.Admin):
            abort(HTTPStatus.FORBIDDEN,
                  error="You don't have the permission to access this",
                  status='FORBIDDEN')

        jti = UserCurrentJWTToken.query.filter_by(user_id=user.id).first()

        if jti:
            print(jti.jti)
            blocklist = TokenBlocklist(jti=jti.jti)
            db.session.add(blocklist)
            db.session.delete(jti)

        db.session.delete(user)
        db.session.commit()

        return success_response(code=HTTPStatus.OK,
                                msg='User deleted successfully',
                                status='OK')
