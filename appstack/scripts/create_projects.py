#!/usr/bin/env python3

import os
import requests

doccano_url = os.environ["DOCCANO_ACCESS_URL"]
medcat_url = os.environ["MEDCAT_ACCESS_URL"]

resp = requests.post(
    doccano_url + "/v1/auth-token",
    json={
        "username": os.environ["DOCCANO_USERNAME"],
        "password": os.environ["DOCCANO_PASSWORD"],
    },
)
if resp.status_code != 200:
    raise Exception(f"Could not login to doccano: {resp.status_code} {resp.content}")

j = resp.json()
doccano_headers = {"Authorization": f'Token {j["token"]}'}

resp = requests.get(doccano_url + "/v1/projects", headers=doccano_headers)
resp.raise_for_status()
doccano_projects = resp.json()

medcat_headers = None
medcat_projects = None

if os.environ.get("ENABLE_MEDCAT_TRAINER", "") == "True":

    payload = {
        "username": os.environ["MEDCAT_USERNAME"],
        "password": os.environ["MEDCAT_PASSWORD"],
    }
    resp = requests.post(f"{medcat_url}/api/api-token-auth/", json=payload)

    if resp.status_code != 200:
        raise Exception(f"Could not login to medcat: {resp.status_code} {resp.content}")

    j = resp.json()
    medcat_headers = {"Authorization": f'Token {j["token"]}'}

    resp_cdbs = requests.get(f"{medcat_url}/api/concept-dbs/", headers=medcat_headers)
    resp_cdbs.raise_for_status()
    resp_vocabs = requests.get(f"{medcat_url}/api/vocabs/", headers=medcat_headers)
    resp_vocabs.raise_for_status()
    resp_ds = requests.get(f"{medcat_url}/api/datasets/", headers=medcat_headers)
    resp_ds.raise_for_status()
    resp_projs = requests.get(
        f"{medcat_url}/api/project-annotate-entities/", headers=medcat_headers
    )
    resp_projs.raise_for_status()
    medcat_projects = resp_projs.json()["results"]


def get_or_create_doccano_project(projects, name):
    for project in projects:
        if project["name"] == name:
            return project["id"]
    req = {
        "id": 1,
        "name": name,
        "description": name,
        "project_type": "SequenceLabeling",
        "resourcetype": "SequenceLabelingProject",
    }
    resp = requests.post(
        doccano_url + "/v1/projects", json=req, headers=doccano_headers
    )
    resp.raise_for_status()
    return int((resp.json())["id"])


def get_first_result_id(resp):
    return resp["results"][0]["id"]


def get_or_create_medcat_project(projects, name):
    for project in projects:
        if project["name"] == name:
            return project["dataset"]
    cdb_id = get_first_result_id(resp_cdbs.json())
    vocab_id = get_first_result_id(resp_vocabs.json())
    user_id = get_first_result_id(
        requests.get(f"{medcat_url}/api/users/", headers=medcat_headers).json()
    )

    payload = {
        "dataset_name": name,
        "dataset": {"name": {}, "text": {}},
        "description": name
    }

    resp = requests.post(
        f"{medcat_url}/api/create-dataset/",
        json=payload,
        headers=medcat_headers,
    )
    resp.raise_for_status()
    ds_id = resp.json()["dataset_id"]

    # Create the project
    payload = {
        "name": name,
        "description": name,
        "cuis": "",
        "tuis": "",
        "dataset": ds_id,
        "concept_db": cdb_id,
        "vocab": vocab_id,
        "members": [user_id],
    }
    resp = requests.post(
        f"{medcat_url}/api/project-annotate-entities/",
        json=payload,
        headers=medcat_headers,
    )
    resp.raise_for_status()
    return ds_id


project_name_cond = "NHS Health A-Z"
project_name_news = "News"

doccano_project_id_cond = get_or_create_doccano_project(
    doccano_projects, project_name_cond
)
doccano_project_id_news = get_or_create_doccano_project(
    doccano_projects, project_name_news
)

if os.environ.get("ENABLE_MEDCAT_TRAINER", "") == "True":
    medcat_dataset_id_cond = get_or_create_medcat_project(
        medcat_projects, project_name_cond
    )
    medcat_dataset_id_news = get_or_create_medcat_project(
        medcat_projects, project_name_news
    )

print(f"export DOCCANO_PROJECT_ID_COND={doccano_project_id_cond}")
print(f"export DOCCANO_PROJECT_ID_NEWS={doccano_project_id_news}")

if os.environ.get("ENABLE_MEDCAT_TRAINER", "") == "True":
    print(f"export MEDCAT_DATASET_ID_COND={medcat_dataset_id_cond}")
    print(f"export MEDCAT_DATASET_ID_NEWS={medcat_dataset_id_news}")
