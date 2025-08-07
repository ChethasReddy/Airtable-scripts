# Airtable Applicant Processing Scripts

This repository contains Python scripts used to manage and automate applicant data processing with Airtable. These scripts handle tasks like:

- Compressing applicant data from related tables into a single JSON string.
- Decompressing and populating related tables from the compressed applicant data.
- Shortlisting applicants based on predefined rules.
- Enriching applicant records using a local LLM.

## Requirements

- Python 3.8+
- A valid Airtable account and API key
- Your Airtable base must contain the following tables with appropriate fields:
  - Applicants
  - Personal Details
  - Work Experience
  - Salary Preferences
  - Shortlisted Leads (if using the shortlisting script)

## Setup

1. **Install dependencies**  
   Run the following command in your terminal to install the required Python packages:

   ```bash
    pip install -r requirements.txt
   ```

2. **Create a .env file**
   In the root of the project, create a .env file and add the following:

   ```bash
    AIRTABLE_BASE_ID=your_base_id_here
    AIRTABLE_API_KEY=your_airtable_api_key_here
   ```

   Replace the values with your actual Airtable Base ID and API key.

3. **Understand the scripts**
   compression_script.py: Reads linked data from the "Personal Details", "Work Experience", and "Salary Preferences" tables and stores it as a single JSON object in the "Compressed JSON" field of the "Applicants" table.
   decompression_script.py: Reverses the above operation by populating linked tables from the compressed JSON field.
   shortlist_applicants.py: Filters applicants based on location, experience, and compensation criteria, and adds them to the "Shortlisted Leads" table if they meet all requirements.
   llm_enrichment_ollama.py: Sends the compressed JSON of shortlisted applicants to a local LLM LLaMA3 vis Ollama and updates their summary, score, and suggested follow-ups in the Airtable "Applicants" table.
