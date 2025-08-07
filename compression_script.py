import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
TOKEN = os.getenv("AIRTABLE_API_KEY")
HEADERS = {
    'Authorization': f'Bearer {TOKEN}',
    'Content-Type': 'application/json'
}

TABLE_APPLICANTS = 'Applicants'
TABLE_PERSONAL = 'Personal Details'
TABLE_EXPERIENCE = 'Work Experience'
TABLE_SALARY = 'Salary Preferences'


def get_records(table):
    print(f"Fetching records from {table}...")
    url = f'https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{table}'
    records = []
    offset = None

    while True:
        params = {'offset': offset} if offset else {}
        response = requests.get(url, headers=HEADERS, params=params)
        if response.status_code != 200:
            print(f"Failed to fetch from {table}: {response.status_code} - {response.text}")
            return []
        data = response.json()
        records.extend(data['records'])
        offset = data.get('offset')
        if not offset:
            break

    return records


def update_record(table, record_id, field, value):
    url = f'https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{table}/{record_id}'
    payload = {'fields': {field: value}}
    response = requests.patch(url, headers=HEADERS, data=json.dumps(payload))
    if response.status_code != 200:
        print(f"Failed to update {record_id} in {table}: {response.status_code} - {response.text}")


def compress_applicant_data():
    applicants = get_records(TABLE_APPLICANTS)
    if not applicants:
        return

    personal_details = get_records(TABLE_PERSONAL)
    experiences = get_records(TABLE_EXPERIENCE)
    salaries = get_records(TABLE_SALARY)

    for applicant in applicants:
        app_id = applicant['id']
        linked_personal = applicant['fields'].get('Personal Details', [])
        linked_exp = applicant['fields'].get('Work Experience', [])
        linked_salary = applicant['fields'].get('Salary Preferences', [])

        if not (linked_personal and linked_exp and linked_salary):
            continue

        personal = next((r for r in personal_details if r['id'] == linked_personal[0]), None)
        salary = next((r for r in salaries if r['id'] == linked_salary[0]), None)
        exp_list = [r for r in experiences if r['id'] in linked_exp]

        if not (personal and salary and exp_list):
            continue

        json_data = {
            'personal': {
                'name': personal['fields'].get('Full Name'),
                'email': personal['fields'].get('Email'),
                'location': personal['fields'].get('Location'),
                'linkedin': personal['fields'].get('LinkedIn')
            },
            'experience': [
                {
                    'company': e['fields'].get('Company'),
                    'title': e['fields'].get('Title'),
                    'start': e['fields'].get('Start'),
                    'end': e['fields'].get('End'),
                    'technologies': e['fields'].get('Technologies')
                } for e in exp_list
            ],
            'salary': {
                'preferredRate': salary['fields'].get('Preferred Rate'),
                'minimumRate': salary['fields'].get('Minimum Rate'),
                'currency': salary['fields'].get('Currency'),
                'availability': salary['fields'].get('Availability (hrs/wk)')
            }
        }

        json_string = json.dumps(json_data, indent=2)
        update_record(TABLE_APPLICANTS, app_id, 'Compressed JSON', json_string)


compress_applicant_data()
