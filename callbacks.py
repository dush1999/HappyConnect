import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State
import plotly.express as px
import pandas as pd
import datetime
from config import MAGENTA, DARK_GRAY, LIGHT_GRAY, BLUE, DATE_FORMAT
from data_pipeline import all_analyzed_records, TOTAL_EXPECTED_RECORDS, get_outage_df
from ai_client import call_gemini_api

#Data Filtering Function

def get_filtered_dataframe(start_date_str, end_date_str):
    if not all_analyzed_records:
        return pd.DataFrame(), None
        
    df = pd.DataFrame(all_analyzed_records)
    df['date'] = pd.to_datetime(df['date'])
    
    start_date = pd.to_datetime(start_date_str).normalize()
    end_date = pd.to_datetime(end_date_str).normalize() + datetime.timedelta(days=1)
    
    filtered_df = df[
        (df['date'] >= start_date) & 
        (df['date'] < end_date) 
    ].copy()
    
    date_range_str = f"{start_date.strftime('%Y-%m-%d')} to {(end_date - datetime.timedelta(days=1)).strftime('%Y-%m-%d')}"
    return filtered_df, date_range_str


#To render the charts 

def render_charts_and_graphs(filtered_df, outage_df, start_date_str, end_date_str):
    """Generates and returns the charts layout."""

    issue_breakdown = filtered_df.groupby(['issue', 'sentiment', 'source']).size().reset_index(name='Count')
    fig1 = px.bar(
        issue_breakdown, x='Count', y='issue', color='sentiment', 
        facet_col='source', orientation='h', 
        title='1. Customer Issue Volume by Category',
        labels={'issue': 'Root Issue Category', 'Count': 'Total Records'},
        color_discrete_map={'POSITIVE':'#00b800', 'NEGATIVE':MAGENTA, 'NEUTRAL':'#cccccc'},
        height=350
    )
    fig1.update_layout(title_font_color=DARK_GRAY, plot_bgcolor='white', paper_bgcolor='white', margin={'t': 50, 'r': 20, 'l': 20, 'b': 20})
    fig1.update_yaxes(categoryorder='total ascending')


    # 2. NEGATIVE TREND (Time Series)
    negative_df = filtered_df[filtered_df['sentiment'] == 'NEGATIVE'].groupby(filtered_df['date'].dt.date)['record_id'].count().reset_index(name='Count')
    negative_df.rename(columns={'date': 'Date'}, inplace=True)
    fig2 = px.line(
        negative_df, x='Date', y='Count',
        title='2. Daily Trend of NEGATIVE Records',
        labels={'Date': 'Date', 'Count': 'Negative Count'},
        color_discrete_sequence=[MAGENTA],
        markers=True, height=350
    )
    fig2.update_layout(title_font_color=DARK_GRAY, plot_bgcolor='white', paper_bgcolor='white', margin={'t': 50, 'r': 20, 'l': 20, 'b': 20})


    # 3. OUTAGE REPORT (Time Series)
    start_date_str_dt = pd.to_datetime(start_date_str).normalize()
    end_date_str_dt = pd.to_datetime(end_date_str).normalize() + datetime.timedelta(days=1)
    
    filtered_outage_df = outage_df[
        (outage_df['date'] >= start_date_str_dt) & 
        (outage_df['date'] < end_date_str_dt)
    ].copy()
    
    if filtered_outage_df.empty:
        fig3 = px.bar(title='3. Network Outage Reports (No Outages in Range)', height=350)
    else:
        fig3 = px.bar(
            filtered_outage_df, x='date', y='reported_count', color='issue',
            title='3. Network Outage Reports',
            labels={'date': 'Date', 'reported_count': 'Reports Count'},
            color_discrete_sequence=px.colors.qualitative.T10, 
            height=350
        )
    fig3.update_layout(title_font_color=DARK_GRAY, plot_bgcolor='white', paper_bgcolor='white', margin={'t': 50, 'r': 20, 'l': 20, 'b': 20})


    # 4. HAPPY INDEX (Time Series)
    daily_summary = filtered_df.groupby(filtered_df['date'].dt.date)['sentiment'].value_counts().unstack(fill_value=0)
    
    for col in ['POSITIVE', 'NEGATIVE']:
        if col not in daily_summary.columns:
            daily_summary[col] = 0
            
    daily_summary['Total'] = daily_summary.sum(axis=1)
    
    daily_summary['Happy_Index'] = daily_summary.apply(
        lambda row: (row['POSITIVE'] - row['NEGATIVE']) / row['Total'] if row['Total'] > 0 else 0, axis=1
    )
    daily_summary = daily_summary.reset_index()
    daily_summary.rename(columns={'date': 'Date'}, inplace=True)

    fig4 = px.line(
        daily_summary, x='Date', y='Happy_Index',
        title='4. Daily Customer Happy Index',
        labels={'Date': 'Date', 'Happy_Index': 'Index Score'},
        line_shape='spline', markers=True, 
        color_discrete_sequence=[BLUE], 
        height=350
    )
    fig4.update_traces(fill='tozeroy', opacity=0.3)
    fig4.update_yaxes(range=[-1.0, 1.0]) 
    fig4.update_layout(title_font_color=DARK_GRAY, plot_bgcolor='white', paper_bgcolor='white', margin={'t': 50, 'r': 20, 'l': 20, 'b': 20})


    return html.Div(children=[
        html.Div(dcc.Graph(id='issue-breakdown-bar', figure=fig1), 
                 style={'width': '100%', 'marginBottom': '20px', 'padding': '10px', 'backgroundColor': 'white', 'borderRadius': '8px', 'boxShadow': '0 4px 8px rgba(0,0,0,0.05)'}),
        html.Div(style={'display': 'flex', 'gap': '20px', 'marginBottom': '20px'}, children=[
            html.Div(dcc.Graph(id='negative-trend-line', figure=fig2), 
                     style={'flex': 1, 'padding': '10px', 'backgroundColor': 'white', 'borderRadius': '8px', 'boxShadow': '0 4px 8px rgba(0,0,0,0.05)'}),
            html.Div(dcc.Graph(id='outage-report-bar', figure=fig3), 
                     style={'flex': 1, 'padding': '10px', 'backgroundColor': 'white', 'borderRadius': '8px', 'boxShadow': '0 4px 8px rgba(0,0,0,0.05)'}),
        ]),
        html.Div(dcc.Graph(id='happy-index-line', figure=fig4), 
                 style={'width': '100%', 'marginBottom': '20px', 'padding': '10px', 'backgroundColor': 'white', 'borderRadius': '8px', 'boxShadow': '0 4px 8px rgba(0,0,0,0.05)'}),
    ])


def register_callbacks(app):
    """Registers all Dash callbacks with the provided Dash app instance."""
    
    #Main Dashboard

    @app.callback(
        [Output('charts-container', 'children'),
         Output('ai-analysis-output', 'children', allow_duplicate=True), 
         Output('footer-status', 'children')],
        [Input('interval-component', 'n_intervals'),
         Input('manual-refresh-btn', 'n_clicks'),
         Input('date-filter', 'start_date'),
         Input('date-filter', 'end_date')],
        prevent_initial_call=True 
    )
    def update_dashboard_content(n_intervals, refresh_clicks, start_date_str, end_date_str):
        
        if start_date_str is None or end_date_str is None:
            return dash.no_update, dash.no_update, dash.no_update
        
        ctx = dash.callback_context
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else 'initial'
        
        filtered_df, date_range_str = get_filtered_dataframe(start_date_str, end_date_str)
        outage_df = get_outage_df()
        
        charts_content = dash.no_update
        if filtered_df.empty and not all_analyzed_records:
             charts_content = html.Div([
                html.H2("Waiting for data stream to complete...", style={'textAlign': 'center', 'marginTop': '50px'}),
                html.P(f"Processing initial records. Charts will load shortly. (0/{TOTAL_EXPECTED_RECORDS})")
            ])
        elif filtered_df.empty:
             charts_content = html.Div([html.H2("No data found for the selected date range.", style={'textAlign': 'center', 'marginTop': '50px'})])
        else:
            charts_content = render_charts_and_graphs(filtered_df, outage_df, start_date_str, end_date_str)

        
        ai_output_clear = dash.no_update
        if trigger_id in ['date-filter', 'manual-refresh-btn']:
            ai_output_clear = "Press 'Generate AI Analysis' to summarize the current data filter."

        footer_status = f"Last updated: {datetime.datetime.now().strftime('%H:%M:%S')} | Records Processed: {len(all_analyzed_records)}/{TOTAL_EXPECTED_RECORDS} | Filtered Records: {len(filtered_df)}"
        
        return charts_content, ai_output_clear, footer_status


 
    @app.callback(
        Output('ai-analysis-output', 'children'),
        Input('ai-analysis-btn', 'n_clicks'),
        [
            State('date-filter', 'start_date'),
            State('date-filter', 'end_date'),
        ]
    )
    def handle_ai_analysis_request(n_clicks, start_date_str, end_date_str):
        if n_clicks is None or n_clicks == 0:
            return dash.no_update
        
        # Loading State 
        loading_message = html.Div([
            html.Span("Analyst is synthesizing the filtered data... (Wait time is dependent on API response)", 
                      style={'color': MAGENTA, 'fontStyle': 'italic', 'marginLeft': '10px'})
        ], style={'textAlign': 'center', 'padding': '20px'})
        
        # Get the Filtered Data
        filtered_df, date_range_str = get_filtered_dataframe(start_date_str, end_date_str)
        
        # Call the Gemini API
        analysis_text = call_gemini_api(filtered_df, date_range_str)
        
        return dcc.Markdown(analysis_text)