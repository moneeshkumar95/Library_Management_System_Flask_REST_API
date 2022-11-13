from app import Blueprint, Api, api
from .views.user_auth_api import UserRegisterAPI, UserAuthenticationAPI, LogoutAPI, PasswordChange, UserActivationAPI
from .views.user_api import UserListAPI, UserAPI
from .views.category_api import CategoryCreateListAPI, CategoryAPI
from .views.book_api import BookCreateListAPI, BookAPI, BorrowBookAPI, ReturnBookAPI, BookReviewAPI, MyBookAPI, HistoryAPI

# User auth Blueprint
bp_user_auth = Blueprint('bp_user_auth', __name__, url_prefix='/api/user')
api_user_auth = Api(bp_user_auth)

# User Blueprint
bp_user = Blueprint('bp_user', __name__, url_prefix='/api/user')
api_user = Api(bp_user)

# Category Blueprint
bp_category = Blueprint('bp_category', __name__, url_prefix='/api/category')
api_category = Api(bp_category)

# Book Blueprint
bp_book = Blueprint('bp_book', __name__, url_prefix='/api/book')
api_book = Api(bp_book)


# User auth urls
api_user_auth.add_resource(UserRegisterAPI, '/register', methods=['POST'])
api_user_auth.add_resource(UserAuthenticationAPI, '/login', methods=['POST'])
api_user_auth.add_resource(LogoutAPI, '/logout', methods=['DELETE'])
api_user_auth.add_resource(PasswordChange, '/password_change', methods=['PUT'])
api_user_auth.add_resource(UserActivationAPI, '/activation/<_id>', methods=['PUT'])

# User urls
api_user.add_resource(UserListAPI, '', methods=['GET'])
api_user.add_resource(UserAPI, '/<_id>', methods=['GET', 'PUT', 'DELETE'])

# Category urls
api_category.add_resource(CategoryCreateListAPI, '', methods=['GET', 'POST'])
api_category.add_resource(CategoryAPI, '/<_id>', methods=['GET', 'PUT', 'DELETE'])

# Book urls
api_book.add_resource(BookCreateListAPI, '', methods=['GET', 'POST'])
api_book.add_resource(BookAPI, '/<_id>', methods=['GET', 'PUT', 'DELETE'])
api_book.add_resource(BorrowBookAPI, '/borrow/<_id>', methods=['GET'])
api_book.add_resource(ReturnBookAPI, '/return/<_id>', methods=['GET'])
api_book.add_resource(BookReviewAPI, '/review/<_id>', methods=['POST', 'PUT'])

# My book
api.add_resource(MyBookAPI, '/my_books', methods=['GET'])

# History
api.add_resource(HistoryAPI, '/history', methods=['GET'])
