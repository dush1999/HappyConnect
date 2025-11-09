import datetime

# GEMINI CONFIGURATION
API_KEY = "AIzaSyDGB2v6Bq4cvdYB45jO663-EfckggqhQhg" 
GEMINI_MODEL = "gemini-2.5-flash-preview-09-2025"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={API_KEY}"

MAGENTA = '#e20074'
DARK_GRAY = '#333333'
LIGHT_GRAY = '#f4f4f4'
BLUE = '#00B0FF'

#This is for the data generation
NUM_DAYS = 15
NARRATIVE_START_DATE = datetime.date(2025, 10, 1) 
DATE_FORMAT = "%Y-%m-%d"