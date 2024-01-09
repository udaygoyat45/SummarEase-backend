import requests
from celery import shared_task, group
from celery.contrib.abortable import AbortableTask
from app import socketio, db, config
from celery.utils.log import get_task_logger
import urllib.parse
from openai import OpenAI
from openai._exceptions import RateLimitError
import time

client = OpenAI()
logger = get_task_logger(__name__)

def summarize_content(content):
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        messages=[
            {"role": "system", "content": "Act as an expert on summarization, outlining and structuring. Your style of writing should be informative and logical. Provide me with a summary of the content posted by me. The summary should include as much content as possible while keeping it lucid and easy to understand."},
            {"role": "user", "content": content}
        ]
    )

    return completion.choices[0].message.content

# @shared_task(bind=True, base=AbortableTask)
# def llm_completion(self, instruction, content):
#     prompt = ""
#     if instruction is not None:
#         prompt += f"\n\n### Instructions: \n{instruction}"
#     if content is not None:
#         prompt += f"\n\n### Content: \n{content}"

#     prompt += f"\n\n### Response:\n"

#     response = requests.post(urllib.parse.urljoin(config.LLM_API_URI, '/v1/completions'), json={
#         "prompt": prompt,
#         "max_tokens": 2000,
#         "temperature": 0,
#     })

#     response_data = response.json()
#     return response_data['choices'][0]['text']


def create_chunks(long_text, chunk_size=1000):
    word_list = long_text.split(' ')
    chunks = []
    i = 0
    while i < len(word_list):
        chunks.append(' '.join(word_list[i:i+chunk_size]))
        i += chunk_size

    return chunks


@shared_task(base=AbortableTask)
def generate_summary(book_id, user_id):
    curr_book = db.books.find_one({'ID': book_id})
    if curr_book is None:
        socketio.emit('book_progress', {'error': 'Book not found'}, to=user_id)
        return

    if 'text' not in curr_book or curr_book['text'] is None or len(curr_book['text']) == 0:
        socketio.emit('book_progress', {'error': 'Could not find text of book'}, to=user_id)
        return
    
    if 'summary' in curr_book and curr_book['summary'] is not None and len(curr_book['summary']) > 0:
        for i, curr_summary in enumerate(curr_book['summary']):
            socketio.emit('summary_chunk', curr_summary, to=user_id)
            socketio.emit('book_progress', {
                'message': 'Summary generation in progress...',
                'progress': 50 + (i + 1) / len(curr_book['summary']) * 50}, to=user_id)

        return curr_book['summary']


    logger.info('GENERATE SUMMARY WAS CALLED')
    book_chunks = create_chunks(curr_book['text'], chunk_size=7000)
    summary_chunks = []

    socketio.emit('book_progress', {'message': 'Starting to summarize the book...', 'progress': 50}, to=user_id)

    for i, chunk in enumerate(book_chunks):
        curr_summary = None
        try:
            curr_summary = summarize_content(chunk)
            # Personal LLAMA.cpp LLM Model
            # curr_summary = llm_completion("Please summarize the content below.", chunk)
        except RateLimitError as e:
            socketio.emit("book_progress", {'message': "API rate limit has reached... Please wait a few minutes. You can keep this page running in the background"}, to=user_id)
            time.sleep(60)

            try:
                curr_summary = summarize_content(chunk)
            except Exception as e:
                socketio.emit("book_progress", {'error': "There was an error generating the summary. Please try again later."}, to=user_id)
                return

        except Exception as e:
            logger.info('ERROR', e)
            socketio.emit("book_progress", {'error': "There was an error generating the summary. Please try again later."}, to=user_id)
            return

        if curr_summary is not None:
            summary_chunks.append(curr_summary)
        else:
            socketio.emit("book_progress", {'error': "There was an error generating the summary. Please try again later."}, to=user_id)
            return

        logger.info(f'Chunk {i}: {user_id}')
        socketio.emit('summary_chunk', curr_summary, to=user_id)
        socketio.emit('book_progress', {
            'message': 'Summary generation in progress...',
            'progress': 50 + (i + 1) / len(book_chunks) * 50}, to=user_id)


    db.books.update_one({'ID': book_id}, {'$set': {'summary': summary_chunks}})
    socketio.emit('book_progress', {'message': 'Generating summary finished', 'progress': 100}, to=user_id)
    return summary_chunks
