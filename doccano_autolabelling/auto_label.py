#!./run_python.sh

import os, sys
import re
import requests


class Client(object):

    def __init__(self, entrypoint=None, username=None, password=None):
        self.entrypoint = entrypoint
        self.client = requests.Session()
        resp = self.client.post(f'{entrypoint}/v1/auth-token',
            json={
            "username": username,
            "password": password,
            }
        )
        resp.raise_for_status()
        token = resp.json()["token"]
        self.client.headers.update({'Authorization': f'Token {token}'})

    def fetch_projects(self):
        url = f'{self.entrypoint}/v1/projects'
        response = self.client.get(url)
        return response

    def create_project(self, name, description, project_type):
        mapping = {'SequenceLabeling': 'SequenceLabelingProject',
                   'DocumentClassification': 'TextClassificationProject',
                   'Seq2seq': 'Seq2seqProject'}
        data = {
            'name': name,
            'project_type': project_type,
            'description': description,
            'guideline': 'Hello',
            'resourcetype': mapping[project_type]
        }
        url = f'{self.entrypoint}/v1/projects'
        response = self.client.post(url, json=data)
        return response.json()

    def fetch_documents(self, project_id):
        url = f'{self.entrypoint}/v1/projects/{project_id}/docs'
        result = self.client.get(url)

        while True:
            result.raise_for_status()
            result = result.json()
            docs = result['results']
            next_url = result.get('next')
            for doc in docs:
                yield doc
            if next_url is None:
                break
            print(f'Requesting {next_url}')
            result = client.client.get(next_url)

    def add_document(self, project_id, text):
        data = {
            'text': text
        }
        url = f'{self.entrypoint}/v1/projects/{project_id}/docs'
        response = self.client.post(url, json=data)
        return response.json()

    def fetch_labels(self, project_id):
        url = f'{self.entrypoint}/v1/projects/{project_id}/labels'
        response = self.client.get(url)
        return response.json()

    def add_label(self, project_id, text):
        data = {
            'text': text
        }
        url = f'{self.entrypoint}/v1/projects/{project_id}/labels'
        response = self.client.post(url, json=data)
        return response.json()

    def fetch_annotations(self, project_id, doc_id):
        url = f'{self.entrypoint}/v1/projects/{project_id}/docs/{doc_id}/annotations'
        response = self.client.get(url)
        return response.json()

    def annotate(self, project_id, doc_id, data):
        url = f'{self.entrypoint}/v1/projects/{project_id}/docs/{doc_id}/annotations'
        response = self.client.post(url, json=data)
        return response.json()


# A very dummmy annotator. Should be replaced by a real one (like HELIN, see https://github.com/cambridgeltl/HELIN#technical-tidbits)
def annotate(text):
    pattern = re.compile(r'\b(testing)\b')
    pos = 0
    result = []
    while pos < len(text):
        match = pattern.search(text, pos)
        if not match:
            break
        start = match.start()
        end = match.end()
        result.append({
            'start_offset': start,
            'end_offset': end,
            'label': match.group(1),
            'prob': 0.8,
        })
        pos = end + 1
    return result

if __name__ == '__main__':
    project_id = sys.argv[1]
    client = Client(os.environ["DOCCANO_ACCESS_URL"], username=os.environ["DOCCANO_USERNAME"], password=os.environ["DOCCANO_PASSWORD"])
    labels = client.fetch_labels(project_id)
    labels_map = {item['text']: item for item in labels}

    labels_added = 0
    docs_scanned = 0
    docs_annotated = 0
    for doc in client.fetch_documents(project_id):
        if not doc.get('annotations'):
            # Found an unannotated document, annotate it
            labels = annotate(doc['text'])

            for label in labels:
                label_text = label['label']
                existing_label = labels_map.get(label_text)
                if not existing_label:
                    existing_label = client.add_label(project_id, label_text)
                    labels_map[label_text] = existing_label
                    labels_added += 1
                data = {
                    'start_offset': label['start_offset'],
                    'end_offset': label['end_offset'],
                    'label': existing_label['id'],
                    'prob': label['prob'],
                }
                client.annotate(project_id=project_id,
                    doc_id=doc['id'],
                    data=data)

            docs_annotated += 1
        docs_scanned += 1

    print(f"Documents scanned:\t{docs_scanned}")
    print(f"Documents annotated:\t{docs_annotated}")
    print(f"Labels added:\t\t{labels_added}")
