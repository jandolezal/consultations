#!/usr/bin/env python3

"""Scrapes feedback to a public consutation by the EC
https://ec.europa.eu/info/law/better-regulation/brpapi/allFeedback?
Uses params publicationId, size and page to iterate over all feedback
"""

import os
import sqlite3
import json
import random
import time
import requests

headers = {
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:83.0) Gecko/20100101 Firefox/83.0'
    }


def get_total_pages(url, params):
    # Get total number of pages
    r = requests.get(url, params=params, headers=headers, timeout=12)
    if r.status_code == requests.codes.ok:
        json_resp = json.loads(r.text)
        total_pages = json_resp['page']['totalPages']
        return total_pages
    return 0


def reduce_attachments(response):
    # Extract only first attachment url and its name
    try:
        att_base_url = 'https://ec.europa.eu/info/law/better-regulation/api/download/'
        att_id = response['attachments'][0]['documentId']
        att_name = response['attachments'][0]['ersFileName']
        if att_id:
            response['attachmentUrl'] = att_base_url + att_id
            response['ersFileName'] = att_name
        else:
            response['attachmentUrl'] = None
            response['ersFileName'] = None
    except IndexError:
        # No attachments, move on
        response['attachmentUrl'] = None
        response['ersFileName'] = None
        pass
    response.pop('attachments', None)
    response.pop('_links', None)


def parse_page(page_number, url, params):
    feedback = []
    # By defaul each page has 20 items (feedbacks).
    params.update({'page': page_number})
    r = requests.get(url, params=params, headers=headers, timeout=15)

    if r.status_code == requests.codes.ok:
        json_resp = json.loads(r.text)

        # List with dictionaries
        current_feedback = json_resp['_embedded']['feedbackV1']

        # Each response is a dictionary
        for response in current_feedback:
            # Processing dictionary within the list
            reduce_attachments(response)

        feedback.extend(current_feedback)
        print(f'Current page: {page_number}')
        print(f"Feedbacks per page: {params['size']}")
    else:
        with open('skipped_pages.txt', 'a') as fout:
            fout.write(page_number + '\n')

    return feedback


def scrape(url, id, directory, db_name):
    params = {
        'publicationId': id,
        'size': 20,
        }

    total_pages = get_total_pages(url, params)

    db_path = os.path.join(os.path.abspath(directory), db_name)
    conn = sqlite3.connect(db_path)
    curs = conn.cursor()

    curs.execute("""CREATE TABLE feedback
    (id INT PRIMARY KEY,
    publication_id INT,
    reference_initiative VARCHAR(64),
    date_feedback VARCHAR(64),
    language VARCHAR(6),
    country VARCHAR(3),
    organization VARCHAR(128),
    first_name VARCHAR(128),
    surname VARCHAR(128),
    user_type VARCHAR(128),
    company_size VARCHAR(64),
    attachment_url VARCHAR(128),
    attachment_filename VARCHAR(128),
    feedback TEXT
    )
    """)

    for page_number in range(total_pages):
        feedback = parse_page(page_number, url, params)

        reordered_feedback = []

        for f in feedback:
            new_order = [
                'id', 'publicationId', 'referenceInitiative',
                'dateFeedback', 'language', 'country', 'organization',
                'firstName', 'surname', 'userType', 'companySize',
                'attachmentUrl', 'ersFileName', 'feedback',
            ]
            reordered_feedback.append([f[k] for k in new_order])

        curs.executemany('INSERT INTO feedback VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)', reordered_feedback)
        conn.commit()

        if total_pages % 50 == 0:
            time.sleep(random.randint(1, 3))

    curs.close()
    conn.close()


if __name__ == '__main__':
    directory = 'taxonomy'
    URL = 'https://ec.europa.eu/info/law/better-regulation/brpapi/allFeedback?'
    scrape(URL, 16015203, directory, 'taxonomy.db')
