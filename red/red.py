#!/usr/bin/env python

"""Scrapes feedback to a public consutation by the EC
by documentId. There is an undocumented json API at 
https://ec.europa.eu/info/law/better-regulation/brpapi/allFeedback?
"""

import csv
import json
import requests


def get_total_pages(url, params):
    # Get total number of pages
    r = requests.get(url, params=params)
    json_resp = json.loads(r.text)
    pages = json_resp['page']['totalPages']
    return pages


def parse_feedback(url, params, pages):
    feedback = []
    
    # By defaul each page has 20 items
    for page in range(0, pages):
        params.update(dict(page=page))
        r = requests.get(url, params=params)
        json_resp = json.loads(r.text)
        
        # List with dictionaries
        page = json_resp['_embedded']['feedbackV1']
        # Each response as a dictionary
        for response in page:
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
        
        feedback.extend(page)
        print(f'Current page feedbacks: {len(page)}')
        print(f'Total feedbacks so far: {len(feedback)}')
    
    return feedback


def to_csv(feedback, file):
    with open(file, 'w') as csvfile:
        fieldnames = set(feedback[0].keys())
        fieldnames.add('attachmentUrl')
        fieldnames.add('ersFileName')
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(feedback)


def scrape(URL, id):
    params = dict(publicationId=id)
    total_pages = get_total_pages(URL, params)
    feedback = parse_feedback(URL, params, total_pages)
    to_csv(feedback, 'red.csv')


if __name__ == '__main__':
    URL = 'https://ec.europa.eu/info/law/better-regulation/brpapi/allFeedback?'
    scrape(URL, id=8285038)
