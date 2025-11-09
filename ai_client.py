import requests
import time
import json
import pandas as pd
from config import API_KEY, API_URL

def call_gemini_api(df_to_analyze: pd.DataFrame, date_range_str: str) -> str:
    if not API_KEY:
        return "API Key Missing! Please set the `API_KEY` variable in `config.py` to enable AI analysis."
    
    if df_to_analyze.empty:
        return "No Data for Analysis: The current filter selections returned no records."

    df_gemini = df_to_analyze.tail(50)[['date', 'issue', 'sentiment', 'description', 'source']]
    filtered_data_json = df_gemini.to_json(orient="records", indent=2)

    system_prompt = (
        "You are a Senior Customer Experience Analyst for a major telecom company. "
        "Analyze the provided JSON data of customer contacts (Call Logs and Feedback Forms). "
        "Provide a concise, professional, and actionable report focused on the filter period. "
        "1. **Executive Summary:** A two-sentence summary of the overall sentiment and primary issue during this period. "
        "2. **Key Findings:** Detail the most critical issue, noting any difference between Call Logs and Feedback Forms. "
        "3. **Recommendation:** Offer one specific, immediate action to improve the customer experience."
        "Format your response clearly using markdown headings and bold text."
    )

    user_query = (
        f"Analyze the following recent customer contact data (filtered for {date_range_str}). "
        f"DATA (Top 50 Records):\n```json\n{filtered_data_json}\n```"
    )

    payload = {
        "contents": [{"parts": [{"text": user_query}]}],
        "tools": [{"google_search": {} }],
        "systemInstruction": {"parts": [{"text": system_prompt}]},
    }

    try:
        for attempt in range(3):
            response = requests.post(API_URL, headers={'Content-Type': 'application/json'}, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('candidates') and result['candidates'][0].get('content'):
                    return result['candidates'][0]['content']['parts'][0]['text']
                else:
                    return f"AI Response Error: The API returned an empty or malformed response. Status: {response.status_code}"

            if response.status_code in [429, 500, 503]:
                time.sleep(2 ** attempt) 
            else:
                return f"Analysis Error (HTTP {response.status_code}):{response.reason}."
        
        return "Analysis Failed:** The API failed to return a valid response after multiple attempts."

    except requests.exceptions.RequestException as e:
        return f"Analysis Error (Network):** Could not connect to the API. Details: {e}"
    except Exception as e:
        return f"Analysis Error (General):** An unexpected error occurred: {e}"