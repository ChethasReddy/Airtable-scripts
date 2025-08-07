import requests
import json
from dateutil import parser
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

BASE_ID = os.getenv('AIRTABLE_BASE_ID')
TOKEN = os.getenv('AIRTABLE_API_KEY')
HEADERS = {
    'Authorization': f'Bearer {TOKEN}',
    'Content-Type': 'application/json'
}

TABLE_APPLICANTS = 'Applicants'
TABLE_SHORTLIST = 'Shortlisted Leads'

TIER_1_COMPANIES = ['Google', 'Meta', 'OpenAI', 'Microsoft', 'Amazon']
ALLOWED_COUNTRIES = ['United States', 'United Kingdom', 'Canada', 'India', 'Germany']

def get_records(table):
    url = f'https://api.airtable.com/v0/{BASE_ID}/{table}'
    records = []
    offset = None
    while True:
        params = {'offset': offset} if offset else {}
        response = requests.get(url, headers=HEADERS, params=params)
        if response.status_code != 200:
            print(f"Error fetching from {table}: {response.status_code} - {response.text}")
            break
        data = response.json()
        records.extend(data['records'])
        offset = data.get('offset')
        if not offset:
            break
    return records

def already_shortlisted(applicant_id, existing_shortlists):
    return any(sl['fields'].get('Applicant', [None])[0] == applicant_id for sl in existing_shortlists)

def create_shortlist(applicant_id, compressed_json, reason):
    url = f'https://api.airtable.com/v0/{BASE_ID}/{TABLE_SHORTLIST}'
    payload = {
        "fields": {
            "Applicant": [applicant_id],
            "Compressed JSON": compressed_json,
            "Score Reason": reason
        }
    }
    response = requests.post(url, headers=HEADERS, data=json.dumps(payload))
    if response.status_code == 200:
        print(f"Shortlisted applicant {applicant_id}")
    else:
        print(f"Failed to shortlist {applicant_id}: {response.status_code} - {response.text}")

def parse_date(date_str):
    try:
        return parser.parse(date_str)
    except:
        return None

def calculate_total_experience_years(experience):
    total_days = 0
    for entry in experience:
        start = parse_date(entry.get('start'))
        end = parse_date(entry.get('end')) or datetime.today()
        if start and end:
            total_days += (end - start).days
    return total_days / 365.0

def shortlist_applicants():
    applicants = get_records(TABLE_APPLICANTS)
    existing_shortlists = get_records(TABLE_SHORTLIST)

    for applicant in applicants:
        applicant_id = applicant['id']
        fields = applicant.get('fields', {})
        compressed_json = fields.get('Compressed JSON')

        if not compressed_json or already_shortlisted(applicant_id, existing_shortlists):
            continue

        try:
            data = json.loads(compressed_json)
        except Exception as e:
            print(f"Invalid JSON for {applicant_id}: {e}")
            continue

        personal = data.get('personal', {})
        experience = data.get('experience', [])
        salary = data.get('salary', {})

        total_years = calculate_total_experience_years(experience)
        has_tier1 = any(e.get('company', '').strip() in TIER_1_COMPANIES for e in experience)
        experience_ok = total_years >= 4 or has_tier1

        preferred_rate = salary.get('preferredRate')
        availability = salary.get('availability')
        compensation_ok = preferred_rate is not None and availability is not None and preferred_rate <= 100 and availability >= 20

        location = personal.get('location', '').strip()
        location_ok = location in ALLOWED_COUNTRIES

        if experience_ok and compensation_ok and location_ok:
            reason = []
            if has_tier1:
                reason.append("Worked at Tier-1 company")
            if total_years >= 4:
                reason.append(f"{total_years:.1f} years experience")
            reason.append(f"Rate: ${preferred_rate}/hr, Availability: {availability} hrs/week")
            reason.append(f"Location: {location}")
            create_shortlist(applicant_id, compressed_json, "; ".join(reason))

shortlist_applicants()
