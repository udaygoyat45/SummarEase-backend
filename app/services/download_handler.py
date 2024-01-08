from app import db

import requests
import fitz
from tqdm import tqdm
from bs4 import BeautifulSoup
import ebooklib
from celery import shared_task
from celery.utils.log import get_task_logger
from celery.contrib.abortable import AbortableTask
from ebooklib import epub
from app import db, socketio

logger = get_task_logger(__name__)

def download_epub(epub_link, user_id):
    response = requests.get(epub_link, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    downloaded_size = 0

    with open('./data/sample.epub', 'wb') as file, tqdm(total=total_size, unit='B', unit_scale=True, desc='Downloading EPUB') as pbar:
        for i, chunk in enumerate(response.iter_content(chunk_size=1024)):
            if chunk:
                pbar.update(len(chunk))
                downloaded_size += len(chunk)
                file.write(chunk)

            socketio.emit('book_progress', {
                'message': 'Downloading the book.',
                'progress': (1024 * i) / total_size * 50
            }, room=user_id)

    book = epub.read_epub('./data/sample.epub')
    total_text = ''

    chapters = list(book.get_items_of_type(ebooklib.ITEM_DOCUMENT))
    for chapter in chapters:
        soup = BeautifulSoup(chapter.get_body_content(), 'html.parser')
        text = [para.get_text() for para in soup.find_all(['p', 'h1', 'div'])]
        total_text += ' '.join(text)

    return total_text
        
        
def download_pdf(pdf_link, user_id):
    response = requests.get(pdf_link, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    downloaded_size = 0
    pdf_content = bytearray()

    with tqdm(total=total_size, unit='B', unit_scale=True, desc='Downloading PDF') as pbar:
        for i, chunk in enumerate(response.iter_content(chunk_size=1024)):
            if chunk:
                pbar.update(len(chunk))
                downloaded_size += len(chunk)
                pdf_content += chunk

            socketio.emit('book_progress', {
                'message': 'Downloading the book.',
                'progress': (1024 * i) / total_size * 50
            }, room=user_id)

        pdf_document = fitz.open(stream=pdf_content, filetype="pdf")
        text_content = ""
        for page_num in range(pdf_document.page_count):
            page = pdf_document[page_num]
            text_content += page.get_text()

        pdf_document.close()
        return text_content
    

@shared_task(bind=True, base=AbortableTask)
def download_book(self, links, book_id, user_id):
    curr_book = db.books.find_one({'ID': book_id})
    if curr_book is None:
        socketio.emit('book_progress', {'error': 'Book not found. Please try again later.'}, room=user_id)
        return

    logger.info("Book:", curr_book)
    if 'text' in curr_book and curr_book['text'] is not None and len(curr_book['text']) != 0:
        socketio.emit('book_progress', {'message': 'Book downloading finished.', 'progress': 50}, room=user_id)
        return curr_book['text']

    socketio.emit('book_progress', {
        'message': 'Starting downloading the book. This may take a while.',
        'progress': 0
    }, room=user_id)

    book_text = None
    for link in links.values():
        try:
            if link.endswith('.pdf'):
                book_text = download_pdf(link, user_id)
            elif link.endswith('.epub'):
                book_text = download_epub(link, user_id)
        except Exception as e:
            logger.info("Error downloading", e)

        if book_text is not None and len(book_text) > 0:
            break

    if book_text is None:
        socketio.emit('book_progress', {
            'error': "There was an issue downloading the contents of the books. Please try again later."
        }, room=user_id)

    db.books.update_one({'ID': book_id}, {'$set': {'text': book_text}})
    socketio.emit('book_progress', {'message': 'Book downloading finished.', 'progress': 50}, room=user_id)
    return book_text
