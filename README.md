# Libary_Management_System_Flask_REST_API

## App Functionality:

### Admin:
-> Create, Read, Update and Delete all Users<br/>
-> Activate/Deactiavte the Users<br/>
-> View users/book History & search History by username, book_title, type(borrow/return) & date<br/>
-> All the functionality that Librarian & Public do<br/>

### Librarian:
-> Create, Read, Update and Delete only Public users<br/>
-> Activate/Deactiavte only Public users<br/>
-> Create, Read, Update and Delete Category<br/>
-> Create, Read, Update and Delete Book<br/>
-> All the functionality that Public do<br/>

### Public:
-> Update their account<br/>
-> Borrow/Return Book<br/>
-> Search Books by book title, book author, book category, book rating<br/>
-> View thier current borrowed Books<br/>
-> View thier History & search History by book_title, type(borrow/return) & date<br/>

### Authentication:
-> JWT

<br/>

## App Structure:
├── app<br/>
│	├── __init__.py<br/>
│	├── main.py<br/>
│	├── utils.py<br/>
│	└── DB<br/>
│	│   ├── __init__.py<br/>
│	│   ├── models.py<br/>
│	│   └── serializers.py<br/>
│	└── API<br/>
│		├── __init__.py<br/>
│		├── urls.py<br/>
│		└── views<br/>
│		   	├── __init__.py<br/>
│		   	├── book_api.py<br/>
│		   	├── category_api.py<br/>
│		   	├── user_api.py<br/>
│		   	└── user_auth_api.py<br/>
