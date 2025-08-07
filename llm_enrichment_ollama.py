import requests
import ollama
import json
import time
import os
from dotenv import load_dotenv
load_dotenv()

AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_APPLICANTS_TABLE = "Applicants"
AIRTABLE_SHORTLIST_TABLE = "Shortlisted Leads"
AIRTABLE_SHORTLIST_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_SHORTLIST_TABLE}"
AIRTABLE_APPLICANTS_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_APPLICANTS_TABLE}"
HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_API_KEY}",
    "Content-Type": "application/json"
}

def fetch_shortlisted():
    params = {"filterByFormula": "NOT({Compressed JSON} = '')"}
    response = requests.get(AIRTABLE_SHORTLIST_URL, headers=HEADERS, params=params)
    return response.json().get("records", [])

def analyze_with_llama(json_str, retries=3, delay=2):
    prompt = f"""
You are a recruiting analyst. Given this JSON applicant profile, do three things:
1. Provide a concise 75-word summary.
2. Rate overall candidate quality from 1–10 (higher is better).
3. Suggest up to three follow-up questions to clarify any data gaps.

Return exactly:
Summary: <text>
Score: <integer>
Follow-Ups: <bullet list>

Applicant Profile:
{json_str}
"""
    for attempt in range(retries):
        try:
            response = ollama.chat(
                model="llama3",
                messages=[{"role": "user", "content": prompt}]
            )
            return response["message"]["content"]
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(delay * (2 ** attempt))
            else:
                return f"Error: {str(e)}"

def parse_llm_response(text):
    try:
        def clean(s):
            return s.strip().strip("*").strip("-").strip()

        summary = clean(text.split("Summary:")[-1].split("Score:")[0])
        score_raw = clean(text.split("Score:")[-1].split("Follow-Ups:")[0])
        score = int(''.join(filter(str.isdigit, score_raw)))
        score = max(1, min(score, 10))
        followups_raw = text.split("Follow-Ups:")[-1].strip()
        followups_lines = [f"•{clean(line)}" for line in followups_raw.splitlines() if line.strip()]
        followups = "\n".join(followups_lines)
        return summary, score, followups
    except Exception as e:
        print("Failed to parse LLM output:", e)
        return "", 1, ""


def update_applicant_record(applicant_id, summary, score, followups):
    fields = {
        "LLM Summary": summary,
        "LLM Score": score,
        "LLM Follow-Ups": followups
    }
    requests.patch(f"{AIRTABLE_APPLICANTS_URL}/{applicant_id}", headers=HEADERS, json={"fields": fields})

def main():
    records = fetch_shortlisted()
    for rec in records:
        compressed_json = rec["fields"].get("Compressed JSON")
        applicant_links = rec["fields"].get("Applicant")
        if not compressed_json or not applicant_links:
            continue
        applicant_id = applicant_links[0]
        response = analyze_with_llama(compressed_json)
        summary, score, followups = parse_llm_response(response)
        update_applicant_record(applicant_id, summary, score, followups)

if __name__ == "__main__":
    main()
