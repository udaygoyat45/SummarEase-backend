from flask import request, Response, json, Blueprint, jsonify
from app.services import libgen
books = Blueprint("books", __name__)


@books.route("ping")
def ping_test():
    return "API connection working"


@books.route("search/<query>")
def list_books(query):
    curr_books = libgen.search_books(query)
    response = jsonify(curr_books)
    return response


@books.route("info/<book_id>")
def get_book(book_id):
    curr_book = libgen.get_book(book_id)
    response = jsonify(curr_book)
    return response
