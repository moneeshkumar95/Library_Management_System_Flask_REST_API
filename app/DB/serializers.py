from app import mm
from .models import User, Category, Book, History, BookReview


# User Serializer
class UserSerializer(mm.Schema):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'phone', 'user_type', 'first_name', 'last_name', 'full_name', 'address',
                  'is_active', 'created_at', 'book_borrowed')

# Category Serializer
class CategorySerializer(mm.Schema):
    class Meta:
        model = Category
        fields = ('id', 'name', 'created_at', 'updated_at', 'updated_by')

# Book Serializer
class BookSerializer(mm.Schema):
    class Meta:
        model = Book
        fields = ('id', 'title', 'author', 'short_description', 'full_description', 'count',
                  'created_at', 'updated_at', 'updated_by', 'overall_rating', 'total_review')

# History Serializer
class HistorySerializer(mm.Schema):
    class Meta:
        model = History
        fields = ('id', 'user_id', 'book_id', 'user_name', 'book_title', 'date', 'type')


class BookReviewSerializer(mm.Schema):
    class Meta:
        model = BookReview
        fields = ('id', 'rating', 'review', 'create_at')