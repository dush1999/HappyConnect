HappyConnect: T-Mobile Customer Happiness Index

Project Overview

HappyConnect is a real-time Customer Experience (CX) intelligence dashboard built using Python and Dash. It continuously monitors customer sentiment and network health to instantly detect issues and highlight moments of delight.

The key feature is the integration with the Gemini AI API to provide immediate, actionable executive summaries on demand.

Architecture

The application is structured into five clean, modular Python files for maintainability:

app.py: Main application runner.

config.py: Global settings and theme.

data_pipeline.py: Simulates and processes the real-time data stream.

ai_client.py: Handles all interaction with the Gemini AI.

callbacks.py: Contains all the dashboard logic and chart generation.

How to Run Locally

Install dependencies (e.g., pip install dash pandas plotly Flask).

Run the main application file from your terminal:

python app.py

Open the address (usually http://0.0.0.0:5001/) in your browser.
