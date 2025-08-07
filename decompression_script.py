import requests
import json
import os
from dotenv import load_dotenv
from dateutil import parser
from datetime import datetime

load_dotenv()

BASE_ID = os.getenv("AIRTABLE_BASE_ID")
TOKEN = os.getenv("AIRTABLE_API_KEY")
HEADERS = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}

TABLE_APPLICANTS = 'Applicants'
TABLE_PERSONAL = 'Personal Details'
TABLE_EXPERIENCE = 'Work Experience'
TABLE_SALARY = 'Salary Preferences'

def get_records(table):
    url = f'https://api.airtable.com/v0/{BASE_ID}/{table}'
    records = []
    offset = None
    while True:
        params = {'offset': offset} if offset else {}
        r = requests.get(url, headers=HEADERS, params=params)
        if r.status_code != 200:
            print(f"Error fetching from {table}: {r.status_code} - {r.text}")
            break
        data = r.json()
        records.extend(data['records'])
        offset = data.get('offset')
        if not offset:
            break
    return records

def delete_records(table, record_ids):
    for rid in record_ids:
        url = f'https://api.airtable.com/v0/{BASE_ID}/{table}/{rid}'
        requests.delete(url, headers=HEADERS)

def create_record(table, fields):
    url = f'https://api.airtable.com/v0/{BASE_ID}/{table}'
    payload = {'fields': fields}
    r = requests.post(url, headers=HEADERS, data=json.dumps(payload))
    if r.status_code != 200:
        print(f"Failed to create in {table}: {r.status_code} - {r.text}")
    return r.json()

def update_record(table, record_id, fields):
    url = f'https://api.airtable.com/v0/{BASE_ID}/{table}/{record_id}'
    payload = {'fields': fields}
    r = requests.patch(url, headers=HEADERS, data=json.dumps(payload))
    if r.status_code != 200:
        print(f"Failed to update in {table}: {r.status_code} - {r.text}")

def decompress_json():
    applicants = get_records(TABLE_APPLICANTS)
    personal_existing = get_records(TABLE_PERSONAL)
    salary_existing = get_records(TABLE_SALARY)
    experience_existing = get_records(TABLE_EXPERIENCE)

    for applicant in applicants:
        app_id = applicant['id']
        fields = applicant.get('fields', {})
        compressed_json = fields.get('Compressed JSON')
        if not compressed_json:
            continue

        try:
            data = json.loads(compressed_json)
        except Exception as e:
            print(f"Invalid JSON for {app_id}: {e}")
            continue

        personal_match = next((r for r in personal_existing if r['fields'].get('Applicant', [None])[0] == app_id), None)
        personal_data = data.get('personal')
        if personal_data:
            personal_fields = {
                "Full Name": personal_data.get("name"),
                "Email": personal_data.get("email"),
                "Location": personal_data.get("location"),
                "LinkedIn": personal_data.get("linkedin"),
                "Applicant": [app_id]
            }
            if personal_match:
                update_record(TABLE_PERSONAL, personal_match['id'], personal_fields)
            else:
                create_record(TABLE_PERSONAL, personal_fields)

        salary_match = next((r for r in salary_existing if r['fields'].get('Applicant', [None])[0] == app_id), None)
        salary_data = data.get('salary')
        if salary_data:
            salary_fields = {
                "Preferred Rate": salary_data.get("preferredRate"),
                "Minimum Rate": salary_data.get("minimumRate"),
                "Currency": salary_data.get("currency"),
                "Availability (hrs/wk)": salary_data.get("availability"),
                "Applicant": [app_id]
            }
            if salary_match:
                update_record(TABLE_SALARY, salary_match['id'], salary_fields)
            else:
                create_record(TABLE_SALARY, salary_fields)

        exp_data = data.get('experience', [])
        exp_current = [r for r in experience_existing if r['fields'].get('Applicant', [None])[0] == app_id]
        exp_ids = [r['id'] for r in exp_current]
        delete_records(TABLE_EXPERIENCE, exp_ids)

        for exp in exp_data:
            exp_fields = {
                "Company": exp.get("company"),
                "Title": exp.get("title"),
                "Start": exp.get("start"),
                "End": exp.get("end"),
                "Technologies": exp.get("technologies"),
                "Applicant": [app_id]
            }
            create_record(TABLE_EXPERIENCE, exp_fields)

decompress_json()