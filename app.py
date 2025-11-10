import streamlit as st
import pandas as pd
from supabase import create_client
import re
from datetime import datetime
import numpy as np 

# -- Supabase Connection
@st.cache_resource
def init_connection():
    """Initializes a connection to the Supabase client."""
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

# -- Dashboard Data Fetching Function
@st.cache_data(ttl=300)
def fetch_dashboard_data(view_name='league_dashboard'):
    """Fetches data from the league_dashboard view for performance charts."""
    try:
        response = supabase.table(view_name).select("*").order("league", desc=False).order("game_week_start", desc=False).execute()
        
        if not response.data:
            st.warning(f"No data found in the '{view_name}' view.")
            return pd.DataFrame()
            
        df = pd.DataFrame(response.data)
        
        if 'game_week_start' in df.columns:
            df['game_week_start'] = pd.to_datetime(df['game_week_start'])
            
        return df
        
    except Exception as e:
        st.error(f"An error occurred while fetching data from '{view_name}': {e}")
        return pd.DataFrame()


# -- Data Fetching Function (Games/Results)
@st.cache_data(ttl=600)
def fetch_data(table_name):
    """Fetches data from a specified table"""
    try:
        response = supabase.table(table_name).select("*").order("gameday", desc=False).execute()
            
        if not response.data:
            st.warning(f"No data found in the '{table_name}' table.")
            return pd.DataFrame()
            
        df = pd.DataFrame(response.data)
        
        if 'gameday' in df.columns:
            try:
                df['gameday'] = pd.to_datetime(df['gameday'])
            except:
                pass

        return df
        
    except Exception as e:
        st.error(f"An error occurred while fetching data from '{table_name}': {e}")
        return pd.DataFrame()

# -- Header Data Fetching Function (Accuracy Headers)
@st.cache_data(ttl=600)
def fetch_header_data(table_name):
    """Fetches results from a specified table"""
    try:
        response = supabase.table(table_name).select("*").execute()
        
        if not response.data:
            st.warning(f"No data found in the '{table_name}' table.")
            return pd.DataFrame()
            
        df = pd.DataFrame(response.data)
        return df
        
    except Exception as e:
        st.error(f"An error occurred while fetching data from '{table_name}': {e}")
        return pd.DataFrame()

# -- Date format function
def format_gameday(date_str):
    """Formats a date string/object to 'Weekday, Month DD'."""
    try:
        if isinstance(date_str, datetime):
            date_obj = date_str
        elif isinstance(date_str, pd.Timestamp):
            date_obj = date_str.to_pydatetime()
        else:
            date_obj = datetime.strptime(str(date_str).split('T')[0], '%Y-%m-%d')
        return date_obj.strftime('%A, %B %d')
    except (ValueError, TypeError):
        return str(date_str)

# -- Dashboard Component Functions

def render_model_accuracy(league_name, results_df):
    """Renders the model accuracy metrics for a given league."""
    if not results_df.empty:
        ml_accuracy = results_df['moneyline_accuracy'].iloc[0]
        ats_accuracy = results_df['ats_accuracy'].iloc[0]
        total_accuracy = results_df['total_accuracy'].iloc[0]
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Winner Accuracy", f"{ml_accuracy:.1f}%")
        col2.metric("Spread Accuracy", f"{ats_accuracy:.1f}%")
        col3.metric("Total Score Accuracy", f"{total_accuracy:.1f}%")
    else:
        st.warning(f"Could not load {league_name} results data.")
    st.markdown("---")

def render_game_predictions(league, all_data):
    """Renders the game prediction cards for NFL, NBA, CFB, MBB."""
    if all_data.empty:
        st.info(f"No predictions available for {league}.")
        return

    st.header(f"{league} Game Predictions")
    
    if 'matchup' in all_data.columns:
        available_matchups = sorted(all_data['matchup'].unique())
        selected_matchup = st.selectbox("Select a Matchup:", options=["All Matchups"] + available_matchups, index=0, key=f"{league}_matchup_select")
        st.markdown("---")
        
        display_data = all_data if selected_matchup == "All Matchups" else all_data[all_data['matchup'] == selected_matchup]
        
        if not display_data.empty:
            num_columns = 2
            cols = st.columns(num_columns)
            for index, row in display_data.iterrows():
                col_index = index % num_columns
                with cols[col_index]:
                    with st.container(border=True):
                        st.subheader(f"**{row['away_team_name']} @ {row['home_team_name']}**")
                        st.markdown(f"Gameday: **{format_gameday(row['gameday'])}**")
                        team1, team2 = st.columns(2)
                        with team1:
                            st.markdown(f"##### **{row['away_team']}**")
                            st.metric(label="Projected Away Score", value=f"{row['away_sim_points']:.1f}")
                            st.metric(label="Moneyline Odds", value=f"{row['away_ml']}")
                            st.metric(label="Away Spread", value=f"{row['away_spread']}")
                            st.metric(label="Total Under", value=f"{row['total_under']}")
                        with team2:
                            st.markdown(f"##### **{row['home_team']}**")
                            st.metric(label="Projected Home Score", value=f"{row['home_sim_points']:.1f}")
                            st.metric(label="Moneyline Odds", value=f"{row['home_ml']}")
                            st.metric(label="Home Spread", value=f"{row['home_spread']}")
                            st.metric(label="Total Over", value=f"{row['total_over']}")
                        st.markdown("---")
                        st.success(f"Predicted Winner: **{row['pred_winner']}** | {row['pred_wp']} Win Probability")
                        st.success(f"Predicted Cover: **{row['pred_cover_team']}** | {row['pred_ats_prob']} Cover Probability")
                        st.success(f"Predicted Total: **{row['pred_total_name']}** | {row['pred_ou_prob']} O/U Probability")

                        # Insights
                        if isinstance(row.get('insights_v2'), list):
                            with st.expander(f"**{row['pred_winner']} Paths to Victory**", expanded=False):
                                for path in row['insights_v2']:
                                    st.markdown(f"**{path['path']}** ({path['prob']}% Prob)")
                                    st.caption(f"{path['narrative']}")
                                    st.markdown("""<hr style="margin:0.2rem 0;" /> """, unsafe_allow_html=True)
                        
                        if isinstance(row.get('insights_v1'), list):
                            with st.expander(f"**{row['pred_winner']} Score Archetypes**", expanded=False):
                                for path in row['insights_v1']:
                                    st.markdown(f"**{path['path']}** ({path['prob']}% Prob)")
                                    st.caption(f"{path['narrative']}")
                                    st.markdown("""<hr style="margin:0.2rem 0;" /> """, unsafe_allow_html=True)
        else:
            st.info("No predictions available for the selected matchup.")
    else:
        st.error(f"The table for {league} does not contain a 'matchup' column.")
        st.dataframe(all_data)


def render_performance_charts(performance_data):
    """Renders line charts for accuracy and ROI over time using league_dashboard data."""
    st.subheader("Historical Model Performance: Accuracy and Profit")
    
    if performance_data.empty:
        st.info("No historical performance data available from the `league_dashboard` view.")
        return
    
    # -- League Filter for Charts
    leagues = sorted(performance_data['league'].unique())
    selected_leagues = st.multiselect(
        "Select Leagues to Compare:",
        options=leagues,
        default=leagues,
        key='performance_league_filter'
    )
    
    filtered_data = performance_data[performance_data['league'].isin(selected_leagues)].sort_values('game_week_start')

    if filtered_data.empty:
        st.warning("No data found for the selected leagues.")
        return

    st.markdown("---")
    
    # -- Accuracy Chart (Weekly Win Percentage)
    st.markdown("##### Weekly Moneyline Win Percentage")
    accuracy_chart_data = filtered_data.pivot_table(
        index='game_week_start', 
        columns='league', 
        values='weekly_win_pct', 
        aggfunc='mean'
    ) * 100
    st.line_chart(accuracy_chart_data)
    
    st.markdown("---")

    # -- Cumulative Profit Chart (Moneyline)
    st.markdown("##### Cumulative Moneyline Profit (Units)")
    profit_chart_data = filtered_data.pivot_table(
        index='game_week_start', 
        columns='league', 
        values='cumulative_win_profit', 
        aggfunc='mean'
    )
    st.line_chart(profit_chart_data)
    
    # -- Add tabs for ATS/O/U charts
    with st.expander("View Spread (ATS) and Total (O/U) Performance"):
        tab1, tab2 = st.tabs(["Spread (ATS) Performance", "Total (O/U) Performance"])
        
        with tab1:
            st.markdown("###### Weekly ATS Win Percentage")
            ats_acc_chart = filtered_data.pivot_table(
                index='game_week_start', columns='league', values='weekly_ats_pct', aggfunc='mean'
            ) * 100
            st.line_chart(ats_acc_chart)
            st.markdown("###### Cumulative ATS Profit (Units)")
            ats_profit_chart = filtered_data.pivot_table(
                index='game_week_start', columns='league', values='cumulative_ats_profit', aggfunc='mean'
            )
            st.line_chart(ats_profit_chart)
            
        with tab2:
            st.markdown("###### Weekly O/U Win Percentage")
            ou_acc_chart = filtered_data.pivot_table(
                index='game_week_start', columns='league', values='weekly_ou_pct', aggfunc='mean'
            ) * 100
            st.line_chart(ou_acc_chart)
            st.markdown("###### Cumulative O/U Profit (Units)")
            ou_profit_chart = filtered_data.pivot_table(
                index='game_week_start', columns='league', values='cumulative_ou_profit', aggfunc='mean'
            )
            st.line_chart(ou_profit_chart)


# -- Streamlit App Layout

st.set_page_config(page_title="PivotBets Predictions", page_icon="", layout="wide")

# -- Header Area
st.title("PivotBets Dashboard")
st.link_button("Visit PivotBets!", "https://www.pivotbets.com")
st.markdown("---")

# -- Fetch Data (Once)
nfl_results = fetch_header_data('nfl_results')
nba_results = fetch_header_data('nba_results')
cfb_results = fetch_header_data('cfb_results')
mbb_results = fetch_header_data('mbb_results')
league_dashboard_data = fetch_dashboard_data()

# -- Tabs for Main Navigation
home_tab, nfl_tab, nba_tab, cfb_tab, mbb_tab = st.tabs([
    "Homepage", 
    "NFL Games", 
    "NBA Games", 
    "College Football", 
    "Men's College Basketball" # Renamed from "MBB"
])

# -- Homepage Content
with home_tab:
    st.info("The Homepage now displays historical **Accuracy and Profit** over time")
    st.markdown("---")
    
    render_performance_charts(league_dashboard_data)
    
    st.markdown("---")
    
    st.subheader("Overall Model Accuracy")
    
    col_nfl, col_nba, col_cfb, col_mbb = st.columns(4)
    
    with col_nfl:
        st.markdown("###### NFL")
        render_model_accuracy("NFL", nfl_results)

    with col_nba:
        st.markdown("###### NBA")
        render_model_accuracy("NBA", nba_results)
        
    with col_cfb:
        st.markdown("###### College Football")
        render_model_accuracy("College Football", cfb_results)

    with col_mbb:
        st.markdown("###### Men's College Basketball")
        render_model_accuracy("Men's College Basketball", mbb_results)


# -- League Tabs Content

with nfl_tab:
    nfl_data = fetch_data('nfl_games')
    render_game_predictions("NFL", nfl_data)

with nba_tab:
    nba_data = fetch_data('nba_games')
    render_game_predictions("NBA", nba_data)

with cfb_tab:
    cfb_data = fetch_data('cfb_games')
    render_game_predictions("College Football", cfb_data)

with mbb_tab:
    mbb_data = fetch_data('mbb_games')
    render_game_predictions("Men's College Basketball", mbb_data)

# -- Sidebar Content
with st.sidebar:
    st.header("Dashboard Information")
    st.write("This section provides global information or filters that may apply across all tabs.")
    st.markdown("---")
    st.caption("Game and Performance Data is refreshed periodically.")
