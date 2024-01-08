from flask import Blueprint, jsonify, request, Response
from app.services import libgen, download_handler, summary_generator
from celery import chain
from app import db
summary = Blueprint("summary", __name__)


@summary.route("ping")
def ping_test():
    return "API connection working"


# TODO: handle potential errors along the way
@summary.route("book/<book_id>", methods=['POST'])
def summarize_book(book_id):
    curr_userid = None
    if request.method == 'POST':
        post_data = request.get_json()
        curr_userid = post_data['user_id']
    else:
        response = jsonify({"error": "Please specify user_id"})
        return response
    

    print('DEBUGGING USERID:', curr_userid)

    curr_book = db.books.find_one({"ID": book_id})
    if not curr_book:
        response = jsonify({"error": "Book not found"})
        return response

    download_links = libgen.get_download_links(curr_book)
    if not download_links:
        response = jsonify({'error': 'No download links found'})
        return response

    s1 = download_handler.download_book.s(download_links, book_id, curr_userid)
    s2 = summary_generator.generate_summary.s(book_id, curr_userid)
    chain(s1, s2).apply_async()

    return Response(status=202)