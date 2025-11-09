import datetime
import requests
import time
import random
import itertools
import pandas as pd
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk
from config import NARRATIVE_START_DATE, NUM_DAYS, DATE_FORMAT

try:
    nltk.download('vader_lexicon', quiet=True)
except:
    pass

#Golbal fields 
all_analyzed_records = [] 
call_index = 0
feedback_index = 0
record_id_counter = 0

date_range = [NARRATIVE_START_DATE + datetime.timedelta(days=i) for i in range(NUM_DAYS)]
sid = SentimentIntensityAnalyzer()

"Generic outage Data(Sample Data)"
outage_list = [
    {"date": date_range[4].strftime(DATE_FORMAT), "reported_count": 450, "issue": "Total Network Failure"},
    {"date": date_range[5].strftime(DATE_FORMAT), "reported_count": 150, "issue": "4G/5G Slowdown"},
    {"date": date_range[6].strftime(DATE_FORMAT), "reported_count": 75, "issue": "App Log-in Failure"},
]
outage_df = pd.DataFrame(outage_list)
outage_df['date'] = pd.to_datetime(outage_df['date'])


#Helper functions

def create_record(date_str, source, sentiment, description, extra_data={}):
    global record_id_counter 
    record_id_counter += 1
    
    date_obj = datetime.datetime.strptime(date_str, DATE_FORMAT).date()
    record_prefix = "CALL" if source == "Call Log" else "FEEDBACK"
        
    return {
        "record_id": f"{record_prefix}_{record_id_counter}",
        "date": date_obj,
        "user_id": f"{source.split()[0].lower()}_user_{record_id_counter}",
        "description": description,
        "fixed_sentiment": sentiment, 
        "network": extra_data,
        "source": source 
    }

def extract_issue(text):
    keywords = {
        "Network": ["signal", "disconnect", "outage", "coverage", "5g", "data speed", "no service", "zero bars"],
        "Billing": ["bill", "charged", "refund", "payment", "fee", "trade-in", "credit", "compensation"],
        "App/Device": ["app", "crash", "update", "esim", "phone", "tablet", "voicemail", "setup"],
        "Support": ["help", "service", "resolution", "agent", "compliment", "empathetic", "professional"],
        "Other": []
    }
    text_lower = text.lower()
    for issue, words in keywords.items():
        if any(word in text_lower for word in words):
            return issue
    return "Other"


#Manually Crafted Records

HAND_CRAFTED_RECORDS = []

# Days 1-4: Baseline Stability
for i in range(4):
    date_str = date_range[i].strftime(DATE_FORMAT)
    HAND_CRAFTED_RECORDS.extend([
        create_record(date_str, "Call Log", "POSITIVE", "The agent was fantastic, very friendly and helped me set up my new device line without any trouble.", {"latency_ms": random.randint(30, 80)}),
        create_record(date_str, "Call Log", "NEUTRAL", "I called to change my payment method and update my address. Standard procedure.", {"latency_ms": random.randint(60, 100)}),
        create_record(date_str, "Call Log", "NEGATIVE", "My T-Mobile app keeps crashing when I try to view my data usage. Very frustrating user experience.", {"latency_ms": random.randint(100, 200)}),
        create_record(date_str, "Feedback Form", "POSITIVE", "Excellent 5G coverage in downtown area, speeds are consistently fast!"),
        create_record(date_str, "Feedback Form", "NEUTRAL", "The email marketing I received was a little confusing regarding the new plan."),
    ])

# Day 5: Major Network Outage
date_str = date_range[4].strftime(DATE_FORMAT)
for _ in range(8): 
    HAND_CRAFTED_RECORDS.append(
        create_record(date_str, "Call Log", "NEGATIVE", "My phone has zero service, zero bars! This is the worst network reliability I've ever experienced. I need this fixed immediately!", {"latency_ms": 500}), 
    )
HAND_CRAFTED_RECORDS.extend([
    create_record(date_str, "Call Log", "NEGATIVE", "I was on hold for over an hour and then the call dropped! Unacceptable support during a complete network failure.", {"latency_ms": 650}),
    create_record(date_str, "Feedback Form", "NEGATIVE", "Complete network down in my area for 4 hours. No data, no calls. This is a business risk."),
    create_record(date_str, "Feedback Form", "NEGATIVE", "T-Mobile failed us today. Total lack of communication about the system outage."),
])

# Days 6-8: Post-Crisis Recovery
for i in range(5, 8):
    date_str = date_range[i].strftime(DATE_FORMAT)
    HAND_CRAFTED_RECORDS.extend([
        create_record(date_str, "Call Log", "POSITIVE", "I understand there was an outage, but the agent was extremely empathetic and applied a credit for my inconvenience. Thank you!", {"latency_ms": random.randint(80, 150)}),
        create_record(date_str, "Call Log", "NEGATIVE", "I need to know exactly how much credit I will receive for the downtime. I was told two different amounts!", {"latency_ms": random.randint(150, 250)}),
        create_record(date_str, "Call Log", "NEUTRAL", "My signal is back, but my data speed is still slow compared to before the outage.", {"latency_ms": random.randint(100, 180)}),
        create_record(date_str, "Feedback Form", "POSITIVE", "The quick resolution and the proactive credit offered was fantastic customer service."),
        create_record(date_str, "Feedback Form", "NEGATIVE", "The auto-pay failed because of the system issues. I was charged a late fee which is unfair!"),
        create_record(date_str, "Feedback Form", "POSITIVE", "Network is fully functional now. Speeds seem even faster than before the issue."),
    ])

# Days 9-15: New Stable Baseline
for i in range(8, NUM_DAYS):
    date_str = date_range[i].strftime(DATE_FORMAT)
    HAND_CRAFTED_RECORDS.extend([
        create_record(date_str, "Call Log", "POSITIVE", "Just called to upgrade my plan. The agent made the process seamless and explained all the options clearly.", {"latency_ms": random.randint(30, 70)}),
        create_record(date_str, "Call Log", "NEUTRAL", "Checking on the availability of the new iPhone model. Standard inquiry.", {"latency_ms": random.randint(50, 100)}),
        create_record(date_str, "Feedback Form", "POSITIVE", "I'm still impressed by the 5G speed! T-Mobile clearly invested heavily in this."),
        create_record(date_str, "Feedback Form", "POSITIVE", "Resolved my issue through the app's chat feature in under five minutes. Perfect."),
    ])


fixed_call_records = [r for r in HAND_CRAFTED_RECORDS if r['source'] == 'Call Log']
fixed_feedback_records = [r for r in HAND_CRAFTED_RECORDS if r['source'] == 'Feedback Form']
TOTAL_EXPECTED_RECORDS = len(fixed_call_records) + len(fixed_feedback_records)


#Simulated API Endpoints

def live_calls():
    global call_index
    if call_index >= len(fixed_call_records):
        return None
    
    record = fixed_call_records[call_index]
    call_index += 1
    
    date_str = record["date"].strftime(DATE_FORMAT)
    
    return {
        "record_id": record["record_id"],
        "date": date_str,
        "user_id": record["user_id"],
        "description": record["description"],
        "fixed_sentiment": record["fixed_sentiment"], 
        "network": record["network"]
    }

def live_feedback():
    global feedback_index
    if feedback_index >= len(fixed_feedback_records):
        return None
    
    record = fixed_feedback_records[feedback_index]
    feedback_index += 1

    date_str = record["date"].strftime(DATE_FORMAT)

    return {
        "record_id": record["record_id"],
        "date": date_str,
        "user_id": record["user_id"],
        "description": record["description"],
        "fixed_sentiment": record["fixed_sentiment"],
        "network": {} 
    }
#Data Pipeline Core logic
def run_pipeline_consumer():
    global all_analyzed_records
    
    streams = list(itertools.chain.from_iterable(itertools.zip_longest(
        ["call"] * len(fixed_call_records), 
        ["feedback"] * len(fixed_feedback_records), 
        fillvalue=None
    )))
    streams = [s for s in streams if s is not None]

    for stream_type in streams:
        if stream_type == "call":
            data = live_calls()
            source = "Call Log"
        else: 
            data = live_feedback()
            source = "Feedback Form"
            
        if data is None:
            time.sleep(0.1) 
            continue
        
        try:
            sentiment = data.get('fixed_sentiment', 'NEUTRAL')
            score = sid.polarity_scores(data['description'])['compound']
            issue_category = extract_issue(data['description'])
            
            new_record = {
                "record_id": data['record_id'],
                "source": source,
                "date": data['date'],
                "user_id": data['user_id'],
                "description": data['description'],
                "sentiment": sentiment,
                "issue": issue_category,
                "sentiment_score": score,
                "extra_data": f"Latency: {data['network'].get('latency_ms', 'N/A')}ms" if source == 'Call Log' else "N/A"
            }
            all_analyzed_records.append(new_record)
            
            time.sleep(0.05) 
        
        except Exception as e:
            print(f"Error processing record from {source}: {e}.")
            break

    print(f"Pipeline Complete! Final records analyzed: {len(all_analyzed_records)}")

def get_outage_df():
    return outage_df