from . import lg
from app import db

from bson.timestamp import Timestamp
from datetime import datetime

FORMATS = ['pdf', 'epub']
PROJECTION = ['Author', 'ID', 'Title', 'Pages', 'Year', 'Publisher', 'Extension']


def search_books(query):
    prev_query = db.book_queries.find_one({'query': query.lower()})
    if prev_query:
        result_ids = prev_query['results']
        curr_books = list(db.books.find({'ID': {'$in': result_ids}}, PROJECTION))
        for i in range(len(curr_books)):
            curr_books[i].pop('_id')
    else:
        curr_books = lg.search_title(query)
        curr_books = list(filter(lambda x: x['Extension'] in FORMATS, curr_books))
        timestamp = Timestamp(int(datetime.today().timestamp()), 1)
        db.book_queries.insert_one({
            'query': query.lower(),
            'timestamp': timestamp,
            'results': [a['ID'] for a in curr_books]
        })

        for i in range(len(curr_books)):
            db.books.update_one({
                'ID': curr_books[i]['ID']},
                {'$set': curr_books[i]}, upsert=True)
            
    return curr_books


def get_book(book_id):
    book = db.books.find_one({'ID': book_id}, PROJECTION)
    if book:
        book.pop('_id')
    return book


def get_download_links(book):
    if 'download_links' in book:
        return book['download_links']
    
    links = lg.resolve_download_links(book)
    book['download_links'] = links
    db.books.update_one({'ID': book['ID']}, {'$set': book}, upsert=False)
    return links
    
