from flask import request, abort
from flask_jwt_extended import get_jwt_identity
from flask_restful import Resource
from app.DB.models import User, Book, Category, History, BookReview, db
from app.DB.serializers import BookSerializer, BookReviewSerializer, HistorySerializer
from app.utils import auth_required, librarian_access, book_summit, success_response, can_review
from http import HTTPStatus
import json
import datetime


class BookCreateListAPI(Resource):
    """"
    GET, POST
    """

    @librarian_access
    def post(self):
        """
        API for add Category

        Required data: title, author, short_description, full_description, count,
                       category:list in JSON
        :return: Success or error message
        """
        request_data = request.json
        identity = get_jwt_identity()
        current_user = User.get_by_id(identity['id'])

        try:
            title = request_data.get('title').strip().lower()
            author = request_data.get('author').strip().lower()
            short_description = request_data.get('short_description').strip().lower()
            full_description = request_data.get('full_description').strip().lower()
            count = request_data.get('count', 0)
            category_id = request_data.get('category_id', [])

            category = Category.query.filter(Category.id.in_(category_id)).all()
            book = Book(title=title, author=author, short_description=short_description,
                        full_description=full_description, count=count, category=category,
                        added_by=current_user)

            return book_summit(code=HTTPStatus.CREATED,
                               data=book,
                               msg='Book added successfully')
        except AttributeError:
            abort(HTTPStatus.BAD_REQUEST,
                  error="Please provide all the data",
                  status='BAD_REQUEST')

    @auth_required
    def get(self):
        """
        API for the book List

        :return: Book list data
        """
        req_args = request.args.to_dict()
        page_num = int(req_args.get("page_num", 1))
        per_page = int(req_args.get("per_page", 10))
        req_args.pop('page_num', None)
        req_args.pop('per_page', None)
        filters = [Book.count.isnot(0)]

        identity = get_jwt_identity()
        if identity['role'] != User.Public:
            filters[0] = Book.id.isnot(None)

        filter_mapper = {"title": Book.title.contains(req_args.get("title", "")),
                         "author": Book.author.contains(req_args.get("author", "")),
                         "overall_rating": Book.overall_rating >= req_args.get("overall_rating", 0)}

        if 'category' in req_args:
            categories = Category.query.filter(Category.id.in_(req_args.get("category", ).split(','))).all()
            book_ids = set()
            for category in categories:
                book_ids.update([i.id for i in category.books])
            filter_mapper['category'] = Book.id.in_(book_ids)

        for req_arg in req_args:
            filters[0] = filters[0] & filter_mapper.get(req_arg)

        books = Book.query.filter(*filters).order_by(Book.title).paginate(page=page_num, per_page=per_page,
                                                                          error_out=False)
        serializer = BookSerializer(many=True, only=('id', 'title', 'author', 'short_description', 'count', 'overall_rating', 'total_review'))
        data = serializer.dump(books.items)

        return dict(code=HTTPStatus.OK,
                    data=data,
                    msg='Books retrieved successfully',
                    status='OK',
                    previous=books.prev_num,
                    next=books.next_num,
                    total=books.total)


class BookAPI(Resource):
    """"
    GET, PUT, DELETE
    """

    @auth_required
    def get(self, _id):
        """
        API for Book detailed

        Required data: book id in URL
        :return: Book data
        """
        book = Book.get_by_id(_id)
        identity = get_jwt_identity()
        serializer = BookSerializer()
        data = serializer.dump(book)

        if identity['role'] == User.Public:
            current_user = User.get_by_id(identity['id'])
            reviews = []
            reviews_append = reviews.append
            review_serializer = BookReviewSerializer()

            for review in book.review:
                review_data = review_serializer.dump(review)
                review_data['user_name'] = review.user.full_name
                reviews_append(review_data)

            data['reviews'] = sorted(reviews, key=lambda x: x['create_at'], reverse=True)

            if can_review(user_id=identity['id'], book_id=_id):
                data['can_review'] = True

                review_book_ids = current_user.review_book_ids()
                if _id in review_book_ids:
                    data['my_review'] = review_serializer.dump(review_book_ids.get(_id))
                else:
                    data['my_review'] = {}
            else:
                data['can_review'] = False

        data['added_by'] = str(book.added_by)
        data['category'] = str(book.category).replace('[', '').replace(']', '').split(', ')

        return success_response(code=HTTPStatus.OK,
                                data=data,
                                msg='Book retrieved successfully',
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

        book = Book.get_by_id(_id)

        category_id = request_data.get('category_id', book.category)
        if category_id != str(book.category).replace('[', '').replace(']', '').split(', '):
            book.category = Category.query.filter(Category.id.in_(category_id)).all()

        book.title = request_data.get('title', book.title).strip().lower()
        book.author = request_data.get('author', book.author).strip().lower()
        book.short_description = request_data.get('short_description', book.short_description).strip().lower()
        book.full_description = request_data.get('full_description', book.full_description).strip().lower()
        book.count = request_data.get('count', book.count)
        book.updated_by = repr(current_user)
        book.updated_at = datetime.datetime.utcnow()

        return book_summit(code=HTTPStatus.OK,
                           data=book,
                           msg='Book updated successfully')

    @librarian_access
    def delete(self, _id):
        """
        API for delete the Book

        Required data: Book id in URL
        :return: Success or Error response
        """
        book = Book.get_by_id(_id)
        db.session.delete(book)
        db.session.commit()

        return success_response(code=HTTPStatus.OK,
                                msg='Book deleted successfully',
                                status='OK')


class BorrowBookAPI(Resource):
    """"
    GET
    """

    @auth_required
    def get(self, _id):
        """
        API for Book Borrow

        :param _id: Book ID
        :return: Success or Error response
        """
        identity = get_jwt_identity()
        current_user = User.get_by_id(identity['id'])
        book = Book.get_by_id(_id)
        book_borrowed = json.loads(current_user.book_borrowed)

        if _id in book_borrowed:
            abort(HTTPStatus.CONFLICT,
                  error='Book already borrowed',
                  status='CONFLICT')

        if not book.count:
            abort(HTTPStatus.CONFLICT,
                  error='All copies Borrowed out',
                  status='CONFLICT')

        book_borrowed.append(_id)
        book.count -= 1
        current_user.book_borrowed = json.dumps(book_borrowed)
        record = History(user_id=current_user.id, book_id=book.id,
                         book_title=book.title, user_name=current_user.username,
                         type=History.borrow_book)
        db.session.add(record)
        db.session.commit()

        return success_response(code=HTTPStatus.OK,
                                msg='Book borrowed successfully',
                                status='OK')


class ReturnBookAPI(Resource):
    """"
    GET
    """

    @auth_required
    def get(self, _id):
        """
        API for Book Return

        :param _id: Book ID
        :return: Success or Error response
        """
        identity = get_jwt_identity()
        current_user = User.get_by_id(identity['id'])
        book = Book.get_by_id(_id)
        book_borrowed = json.loads(current_user.book_borrowed)

        if _id not in book_borrowed:
            abort(HTTPStatus.FORBIDDEN,
                  error="Book not borrowed yet",
                  status='CONFLICT')

        book.count += 1
        book_borrowed.remove(_id)
        current_user.book_borrowed = json.dumps(book_borrowed)

        record = History(user_id=current_user.id, book_id=book.id,
                         book_title=book.title, user_name=current_user.username,
                         type=History.return_book)
        db.session.add(record)
        db.session.commit()

        return success_response(code=HTTPStatus.OK,
                                msg='Book returned successfully',
                                status='OK')


class MyBookAPI(Resource):
    """"
    GET
    """

    @auth_required
    def get(self):
        """
        API for My Books

        :return: Book data
        """
        req_args = request.args.to_dict()
        page_num = int(req_args.get("page_num", 1))
        per_page = int(req_args.get("per_page", 10))
        identity = get_jwt_identity()
        current_user = User.get_by_id(identity['id'])
        print(current_user.book_borrowed)
        books_query = Book.query.filter(Book.id.in_(json.loads(current_user.book_borrowed))).paginate(page=page_num,
                                                                                                      per_page=per_page,
                                                                                                      error_out=False)
        data = []
        data_append = data.append
        book_serializer = BookSerializer(only=('id', 'title'))

        for book in books_query.items:
            serialized_data = book_serializer.dump(book)
            review_book_ids = current_user.review_book_ids()
            if book.id in review_book_ids:
                review_serializer = BookReviewSerializer()
                serialized_data['my_review'] = review_serializer.dump(review_book_ids.get(book.id))
            else:
                serialized_data['my_review'] = {}

            data_append(serialized_data)

        return dict(code=HTTPStatus.OK,
                    data=data,
                    msg='Successfully retrieved users',
                    status='OK',
                    previous=books_query.prev_num,
                    next=books_query.next_num,
                    total=books_query.total)


class HistoryAPI(Resource):
    """"
    GET
    """

    @auth_required
    def get(self):
        """
        API for book history

        :return: JSON book history data
        """
        req_args = request.args.to_dict()
        page_num = int(req_args.get("page_num", 1))
        per_page = int(req_args.get("per_page", 10))
        req_args.pop('page_num', None)
        req_args.pop('per_page', None)
        identity = get_jwt_identity()
        current_user_id = identity['id']
        attr = {'id', 'book_title', 'date', 'type', 'user_name'}
        filters = [History.id.isnot(None)]

        filter_mapper = {"book_title": History.book_title.contains(req_args.get("book_title", "")),
                         "user_name": History.user_name.contains(req_args.get("user_name", "")),
                         "type": History.type.in_(req_args.get("type", "").split(","))}

        if 'date' in req_args:
            date = req_args.get("date").split(',')
            filter_mapper["date"] = History.date.between(f'{date[0][:10]} 00:00:00', f'{date[1][:10]} 23:59:59')

        if identity['role'] == User.Public:
            filters[0] = History.user_id == current_user_id

        for req_arg in req_args:
            filters[0] = filters[0] & filter_mapper.get(req_arg)

        history = History.query.filter(*filters).order_by(History.date.desc()).paginate(page=page_num,
                                                                                        per_page=per_page,
                                                                                        error_out=False)

        serializer = HistorySerializer(many=True, only=attr)
        data = serializer.dump(history.items)
        return dict(code=HTTPStatus.OK,
                    data=data,
                    msg='Data retrieved successfully',
                    status='OK',
                    previous=history.prev_num,
                    next=history.next_num,
                    total=history.total)


class BookReviewAPI(Resource):
    """
    POST, PUT
    """

    @auth_required
    def post(self, _id):
        """
        API for review the book

        :param : Book ID
        :JSON : rating, review(optional)
        :return: Success or Error response
        """
        identity = get_jwt_identity()
        current_user_id = identity['id']
        current_user = User.get_by_id(current_user_id)
        book = Book.get_by_id(_id)

        if not can_review(user_id=current_user_id, book_id=_id):
            abort(HTTPStatus.FORBIDDEN,
                  error='Since you never borrowed this book, you are not allowed to review it',
                  status='FORBIDDEN')

        review_book_ids = current_user.review_book_ids()
        request_data = request.json

        if _id in review_book_ids:
            abort(HTTPStatus.CONFLICT,
                  error='You all ready reviewed it',
                  status='CONFLICT')

        rating = request_data.get('rating')
        review = request_data.get('review', '').strip()
        book_review = BookReview(rating=rating, review=review, book=book, user=current_user)
        book.total_rating += rating
        book.total_review += 1
        book.overall_rating = round(book.total_rating / book.total_review, 1)
        db.session.add(book_review)
        db.session.commit()

        return success_response(code=HTTPStatus.OK,
                                msg='Review successfully',
                                status='OK')

    @auth_required
    def put(self, _id):
        """
        API for update the book review

        :param : BookReview ID
        :JSON : rating, review(optional)
        :return: Success or Error response
        """
        book_review = BookReview.get_by_id(_id)
        book = Book.get_by_id(book_review.book_id)

        request_data = request.json
        rating = request_data.get('rating')
        review = request_data.get('review', '').strip()

        book.total_rating += rating - book_review.rating
        book.overall_rating = round(book.total_rating / book.total_review, 1)

        book_review.rating = rating
        book_review.review = review

        db.session.commit()

        return success_response(code=HTTPStatus.OK,
                                msg='Review updated successfully',
                                status='OK')
