import threading 
import time
import dash
from dash import dcc
from dash import html
from flask import Flask
from config import MAGENTA, DARK_GRAY, LIGHT_GRAY
from config import NARRATIVE_START_DATE, NUM_DAYS, DATE_FORMAT
from data_pipeline import run_pipeline_consumer
from callbacks import register_callbacks
import datetime

# --- APP SETUP ---

# Initialize Flask and Dash
flask_server = Flask(__name__) 
dash_app = dash.Dash(__name__, server=flask_server, url_base_pathname='/')

# Determine date range for the initial filter setup
date_range = [NARRATIVE_START_DATE + datetime.timedelta(days=i) for i in range(NUM_DAYS)]
min_date = date_range[0].strftime(DATE_FORMAT)
max_date = date_range[-1].strftime(DATE_FORMAT)

# Register all callbacks
register_callbacks(dash_app)

# --- LAYOUT DEFINITION ---

def generate_dashboard_layout():
    return html.Div(style={'backgroundColor': LIGHT_GRAY, 'color': DARK_GRAY, 'fontFamily': 'Inter, sans-serif', 'minHeight': '100vh'}, children=[
        
        dcc.Interval(
            id='interval-component',
            interval=3*1000,
            n_intervals=0
        ),
        
        html.Div(style={'backgroundColor': MAGENTA, 'color': 'white', 'padding': '20px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'}, children=[
            html.H1(children='T-Mobile Customer Experience Dashboard',
                    style={'textAlign': 'center', 'marginBottom': '10px', 'fontWeight': '900'}),
            html.Div(children='Real-Time Sentiment and Network Health Monitoring',
                     style={'textAlign': 'center', 'marginBottom': '20px'}),
            
            html.Div(style={'display': 'flex', 'justifyContent': 'center', 'gap': '20px', 'alignItems': 'center'}, children=[
                html.Label('Date Range Filter:', style={'fontWeight': 'bold'}),
                dcc.DatePickerRange(
                    id='date-filter',
                    min_date_allowed=min_date,
                    max_date_allowed=max_date,
                    start_date=min_date, 
                    end_date=max_date,   
                    display_format='YYYY-MM-DD',
                    style={'color': DARK_GRAY}
                ),
                html.Button('Manual Refresh', id='manual-refresh-btn', n_clicks=0, 
                            style={'backgroundColor': 'white', 'color': MAGENTA, 'border': '1px solid white', 'padding': '8px 15px', 'borderRadius': '4px', 'cursor': 'pointer'}),
                html.Button('Generate AI Analysis', id='ai-analysis-btn', n_clicks=0, 
                            style={'backgroundColor': DARK_GRAY, 'color': 'white', 'border': 'none', 'padding': '8px 15px', 'borderRadius': '4px', 'cursor': 'pointer', 'boxShadow': '0 2px 4px rgba(0,0,0,0.2)'}),
            ])
        ]),
        
        # AI Analysis Panel Container
        html.Div(style={'padding': '20px', 'backgroundColor': 'white', 'borderRadius': '8px', 'boxShadow': '0 4px 8px rgba(0,0,0,0.05)', 'marginTop': '20px', 'margin': '20px'}, children=[
            html.H2("Gemini AI Executive Summary", style={'color': MAGENTA, 'marginBottom': '10px', 'borderBottom': f'2px solid {MAGENTA}', 'paddingBottom': '5px'}),
            html.Div(
                id='ai-analysis-output', 
                children="Press 'Generate AI Analysis' to summarize the current data filter.", 
                style={'minHeight': '100px', 'padding': '15px', 'backgroundColor': LIGHT_GRAY, 'borderRadius': '4px', 'whiteSpace': 'pre-wrap'}
            )
        ]),

        html.Div(id='charts-container', style={'padding': '20px'}), 
        
        html.Div(id='footer-status', style={'textAlign': 'right', 'padding': '10px 20px 10px 20px', 'color': DARK_GRAY})
    ])

dash_app.layout = generate_dashboard_layout

# --- RUN LOGIC ---

def run_pipeline_after_delay():
    time.sleep(1) 
    run_pipeline_consumer()

if __name__ == '__main__':
    pipeline_thread = threading.Thread(target=run_pipeline_after_delay, daemon=True)
    pipeline_thread.start()
    
    # FIX: Changed dash_app.run_server to dash_app.run
    dash_app.run(debug=False, host='0.0.0.0', port=5001)