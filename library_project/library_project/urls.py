"""
URL configuration for library_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# from django.contrib import admin
from django.urls import path
from library_app import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    # ---------------- books urls -------------------------
    path('api/books/add/', views.add_book, name='add_book'),
    path('api/test/', views.simple_view, name='simple_view'),
    path('api/books/', views.get_books, name='get_books'),
    path('api/books/<str:book_id>/', views.get_book, name='get_book'),
    path('api/books/genre/<str:genre>/', views.get_books_by_genre, name='get_books_by_genre'),
    path('api/books/author/<str:author>/', views.get_books_by_author, name='get_books_by_author'),
    path('api/books/reader/<str:reader_id>/', views.get_books_by_reader, name='get_books_by_reader'),
    path('api/books/edit/<str:book_id>/', views.edit_book, name='edit_book'),
    path('api/books/delete/<str:book_id>/', views.delete_book, name='delete_book'),
        # ---------------- transactions urls -------------------------
    path('api/transactions/borrow/', views.borrow_book, name='borrow_book'),
    path('api/transactions/return/', views.return_book, name='return_book'),
    path('api/transactions/<str:transaction_id>/', views.get_transaction, name='get_transaction'),
    path('api/transactions/', views.get_all_transactions, name='get_all_transactions'),
    path('api/transactions/user/<str:user_id>/', views.get_transactions_by_user, name='get_transactions_by_user'),
    path('api/transactions/edit/<str:transaction_id>/', views.edit_transaction, name='edit_transaction'),
    path('api/transactions/delete/<str:transaction_id>/', views.delete_transaction, name='delete_transaction'),
        # ---------------- recommendations urls -------------------------
    path('api/recommendations/<str:user_id>/', views.recommend_book, name='recommend_book'),
    path('api/recommendations/user/<str:user_id>/', views.get_user_recommendations, name='get_user_recommendations'),
    path('api/recommendations/books/', views.get_books_by_recommendations, name='get_books_by_recommendations'),
    path('api/relationships/book/<str:book_id>/', views.get_book_relationships, name='get_book_relationships'),
        # ---------------- cache urls -------------------------
    path('api/books/cache/title/<str:title>/', views.get_books_by_title_cached, name='get_books_by_title'),
    path('api/books/cache/author/<str:author>/', views.get_books_by_author_cached, name='get_books_by_author_cached'),
    path('api/books/cache/genre/<str:genre>/', views.get_books_by_genre_cached, name='get_books_by_genre_cached'),
]
