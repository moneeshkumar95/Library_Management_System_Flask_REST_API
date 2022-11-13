from flask import request, abort
from flask_jwt_extended import get_jwt_identity
from app import Resource
from app.DB.models import User, Category, db
from app.DB.serializers import CategorySerializer
from app.utils import auth_required, librarian_access, category_summit, success_response
from http import HTTPStatus
import datetime


class CategoryCreateListAPI(Resource):
    """"
    GET, POST
    """

    @librarian_access
    def post(self):
        """
        API for add Category

        Required data: name in JSON
        :return: Success or error message
        """
        request_data = request.json
        name = request_data.get('name')
        identity = get_jwt_identity()
        current_user = User.get_by_id(identity['id'])

        if not name:
            abort(HTTPStatus.BAD_REQUEST,
                  error="Category name missing",
                  status='BAD_REQUEST')

        category = Category(name=name.strip().lower(), added_by=current_user)

        return category_summit(code=HTTPStatus.CREATED,
                               data=category,
                               msg='Category added successfully')

    @auth_required
    def get(self):
        """
        API for the Category List

        :return: Category list data
        """
        categories = Category.query.order_by(Category.name).all()
        serializer = CategorySerializer(many=True, only=('id', 'name'))
        data = serializer.dump(categories)

        return success_response(code=HTTPStatus.OK,
                                data=data,
                                msg='Category list retrieved successfully',
                                status='OK')


class CategoryAPI(Resource):
    """"
    GET, PUT, DELETE
    """

    @librarian_access
    def get(self, _id):
        """
        API for Category detailed

        Required data: category id in URL
        :return: Category data
        """
        category = Category.get_by_id(_id)
        serializer = CategorySerializer()
        data = serializer.dump(category)
        data['added_by'] = str(category.added_by)

        return success_response(code=HTTPStatus.OK,
                                data=data,
                                msg='Category retrieved successfully',
                                status='OK')

    @librarian_access
    def put(self, _id):
        """
        API for update the Category

        Required data: Category id in URL and category updated name in JSON
        :return: Success or Error response
        """
        request_data = request.json
        identity = get_jwt_identity()
        current_user = User.get_by_id(identity['id'])
        category = Category.get_by_id(_id)
        name = request_data.get('name', category.name)
        category.name = name.strip().lower()
        category.updated_by = repr(current_user)
        category.updated_at = datetime.datetime.utcnow()

        return category_summit(code=HTTPStatus.OK,
                               data=category,
                               msg='Category updated successfully')

    @librarian_access
    def delete(self, _id):
        """
        API for delete the Category

        Required data: Category id in URL
        :return: Success or Error response
        """
        category = Category.get_by_id(_id)
        db.session.delete(category)
        db.session.commit()

        return success_response(code=HTTPStatus.OK,
                                msg='Category deleted successfully',
                                status='OK')
