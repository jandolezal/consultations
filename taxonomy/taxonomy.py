#!/usr/bin/env python3

"""Scrapes feedback to a public consutation by the EC
https://ec.europa.eu/info/law/better-regulation/brpapi/allFeedback?
Uses params publicationId, size and page to iterate over all feedback
"""

import csv
import json
import requests

headers = {
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:83.0) Gecko/20100101 Firefox/83.0'
    }


def get_total_pages(url, params):
    # Get total number of pages
    r = requests.get(url, params=params, headers=headers, timeout=5)
    if r.status_code == requests.codes.ok:
        json_resp = json.loads(r.text)
        pages = json_resp['page']['totalPages']
        return pages
    return 0


def process_response(response):
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
        pass
    response.pop('attachments', None)
    response.pop('_links', None)


def parse_feedback(url, params, pages):
    feedback = []

    # By defaul each page has 20 items (feedbacks). We use 50 in scrape
    for page in range(pages):

        params.update({'page': page})
        r = requests.get(url, params=params, headers=headers, timeout=5)

        if r.status_code == requests.codes.ok:
            json_resp = json.loads(r.text)

            # List with dictionaries
            current_feedback = json_resp['_embedded']['feedbackV1']

            # Each response is a dictionary
            for response in current_feedback:
                # Processing dictionary within the list
                process_response(response)

            feedback.extend(current_feedback)
            print(f'Current page: {page}')
            print(f"Feedbacks per page: {params['size']}")
            print(f'Total feedbacks so far: {len(feedback)}')
        else:
            print('No response. Skipping this page')

    return feedback


def to_csv(feedback, file):
    with open(file, 'w', newline='') as csvfile:
        fieldnames = set(feedback[0].keys())
        fieldnames.add('attachmentUrl')
        fieldnames.add('ersFileName')
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(feedback)


def scrape(url, id, csv_out):
    params = {
        'publicationId': id,
        'size': 50,
        }
    total_pages = get_total_pages(url, params)
    feedback = parse_feedback(url, params, total_pages)
    to_csv(feedback, csv_out)


if __name__ == '__main__':
    URL = 'https://ec.europa.eu/info/law/better-regulation/brpapi/allFeedback?'
    scrape(URL, id=16015203, csv_out='taxonomy.csv')
