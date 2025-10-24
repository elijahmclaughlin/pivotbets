import streamlit as st
import pandas as pd
from supabase import create_client
import re
from datetime import datetime

# -- Supabase Connection
@st.cache_resource
def init_connection():
    """Initializes a connection to the Supabase client."""
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

# -- Data Fetching Function
@st.cache_data(ttl=600)
def fetch_data(table_name):
    """Fetches data from a specified Supabase table."""
    try:
        if table_name == 'nfl_player_prop':
            response = supabase.table(table_name).select("*").order("player_name", desc=False).execute()
        else:
            response = supabase.table(table_name).select("*").order("gameday", desc=False).execute()
            
        if not response.data:
            st.warning(f"No data found in the '{table_name}' table.")
            return pd.DataFrame()
            
        df = pd.DataFrame(response.data)

        if table_name == 'nfl_player_prop':
            string_stat_cols = ['sim_yards', 'sim_tds', 'boom_prob', 'bust_prob']
            
            for col in string_stat_cols:
                if col in df.columns:
                    df[f'{col}_numeric'] = df[col].astype(str).str.extract(r'(\d+\.?\d*)').astype(float)

            df.fillna(0, inplace=True)

        return df
        
    except Exception as e:
        st.error(f"An error occurred while fetching data from '{table_name}': {e}")
        return pd.DataFrame()

# -- Header Data Fetching Function
@st.cache_data(ttl=600)
def fetch_header_data(table_name):
    """Fetches results from a specified Supabase table."""
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

# -- Streamlit App Layout
st.set_page_config(page_title="PivotBets Predictions", page_icon="🏈", layout="wide")
st.title("PivotBets Sports Predictions")
st.link_button("Visit PivotBets!", "https://www.pivotbets.com")

# -- Fetch Header Data
nfl_results = fetch_header_data('nfl_results')
cfb_results = fetch_header_data('cfb_results')

# -- Sidebar for Filtering
st.sidebar.header("Filter Options")
league = st.sidebar.radio(
    "Select a League:",
    ("NFL", "College Football", "NFL Player Props"),
    horizontal=False 
)

# -- Dynamic Header Based on League Selection
st.markdown("---") 

if league == "NFL":
    st.subheader("NFL Model Accuracy")
    if not nfl_results.empty:
        ml_accuracy = nfl_results['moneyline_accuracy'].iloc[0]
        ats_accuracy = nfl_results['ats_accuracy'].iloc[0]
        total_accuracy = nfl_results['total_accuracy'].iloc[0]
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Winner Accuracy", f"{ml_accuracy:.2f}%")
        col2.metric("Spread Accuracy", f"{ats_accuracy:.2f}%")
        col3.metric("Total Score Accuracy", f"{total_accuracy:.2f}%")
    else:
        st.warning("Could not load NFL results data.")

elif league == "College Football":
    st.subheader("College Football Model Accuracy")
    if not cfb_results.empty:
        ml_accuracy = cfb_results['moneyline_accuracy'].iloc[0]
        ats_accuracy = cfb_results['ats_accuracy'].iloc[0]
        total_accuracy = cfb_results['total_accuracy'].iloc[0]

        col1, col2, col3 = st.columns(3)
        col1.metric("Winner Accuracy", f"{ml_accuracy:.2f}%")
        col2.metric("Spread Accuracy", f"{ats_accuracy:.2f}%")
        col3.metric("Total Score Accuracy", f"{total_accuracy:.2f}%")

# -- Determine table to query based on league selection
if league == "NFL":
    table_to_query = "nfl_games"
elif league == "College Football":
    table_to_query = "cfb_games"
else:
    table_to_query = "nfl_player_prop"

all_data = fetch_data(table_to_query)

# -- Helper function to format the date
def format_gameday(date_str):
    """Formats a 'YYYY-MM-DD' date string to 'Weekday, Month DD'."""
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        return date_obj.strftime('%A, %B %d')
    except (ValueError, TypeError):
        return date_str

# -- Main Content Display
# -- NFL & CFB Game Predictions Block
if (league == "NFL" or league == "College Football") and not all_data.empty:
    st.header(f"{league} Game Predictions")
    
    if 'concat' in all_data.columns:
        available_matchups = sorted(all_data['concat'].unique())
        selected_matchup = st.sidebar.selectbox("Select a Matchup:", options=["All Matchups"] + available_matchups, index=0)
        st.markdown("---")
        
        display_data = all_data if selected_matchup == "All Matchups" else all_data[all_data['concat'] == selected_matchup]
        
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

                        # Win Path Insights
                        if isinstance(row['insights_v2'], list):
                            with st.expander(f"**{row['pred_winner']} Paths to Victory**", expanded=False):
                                for path in row['insights_v2']:
                                    st.markdown(f"**{path['path']}** ({path['prob']}% Prob)")
                                    st.caption(f"{path['narrative']}")
                                    st.markdown("""<hr style="margin:0.2rem 0;" /> """, unsafe_allow_html=True)
                            
                        # Score Archetypes
                        if isinstance(row['insights_v1'], list):
                            with st.expander(f"**{row['pred_winner']} Score Archetypes**", expanded=False):
                                for path in row['insights_v1']:
                                    st.markdown(f"**{path['path']}** ({path['prob']}% Prob)")
                                    st.caption(f"{path['narrative']}")
                                    st.markdown("""<hr style="margin:0.2rem 0;" /> """, unsafe_allow_html=True)
                        
        else:
            st.info("No predictions available for the selected matchup.")
    else:
        st.warning(f"The table '{table_to_query}' does not contain a 'concat' column.")
        st.dataframe(all_data)

# -- NFL Player Prop Block
elif league == "NFL Player Props" and not all_data.empty:
    st.header("NFL Player Prop Predictions")
    if 'matchup' in all_data.columns:
        available_matchups = sorted(all_data['matchup'].unique())
        selected_matchup = st.sidebar.selectbox("Select a Matchup:", options=["All Matchups"] + available_matchups, index=0)
        st.markdown("---")
        matchups_to_display = available_matchups if selected_matchup == "All Matchups" else [selected_matchup]

        for matchup in matchups_to_display:
            matchup_data = all_data[all_data['matchup'] == matchup]
            if matchup_data.empty: continue

            teams = matchup_data['team'].unique()
            if len(teams) < 2: continue
            
            # Use regex to be safe
            match = re.search(r'(.+) @ (.+)', matchup)
            if not match: continue
            
            away_team_abbr, home_team_abbr = match.groups()
            away_team = next((t for t in teams if away_team_abbr in t), teams[0])
            home_team = next((t for t in teams if home_team_abbr in t), teams[1])

            # Get the gameday
            gameday_str = matchup_data['gameday'].iloc[0] if not matchup_data.empty else 'Unknown Date'

            with st.container(border=True):
                st.subheader(f"**{matchup}**")
                st.markdown(f"Gameday: **{format_gameday(gameday_str)}**")
                col1, col2 = st.columns(2)

                # Function to display player stats to avoid repeating code
                def display_player_stats(column, team_name, team_data):
                    with column:
                        st.markdown(f"#### {team_name}")
                        unique_players = team_data['player_name'].unique()
                        for player_name in unique_players:
                            with st.expander(f"**{player_name}**"):
                                player_stats = team_data[team_data['player_name'] == player_name]
                                for _, stat_row in player_stats.iterrows():
                                    stat_category_text = stat_row['sim_yards']
                                    category_title = "Stats"
                                    if 'pass' in stat_category_text.lower(): category_title = "Passing"
                                    elif 'rush' in stat_category_text.lower(): category_title = "Rushing"
                                    elif 'rec' in stat_category_text.lower(): category_title = "Receiving"
                                        
                                    st.markdown(f"**{category_title} Projections**")
                                    
                                    st.metric(label="Simulated Yards", value=f"{stat_row['sim_yards_numeric']:.1f}")
                                    st.metric(label="Simulated TDs", value=f"{stat_row['sim_tds_numeric']:.2f}")
                                    st.metric(label="Boom Probability", value=f"{stat_row['boom_prob_numeric']:.1f}%")
                                    st.metric(label="Bust Probability", value=f"{stat_row['bust_prob_numeric']:.1f}%")
                                    st.markdown("""<hr style="margin:0.5rem 0;" /> """, unsafe_allow_html=True)
                
                # Display for both teams
                display_player_stats(col1, away_team, matchup_data[matchup_data['team'] == away_team])
                display_player_stats(col2, home_team, matchup_data[matchup_data['team'] == home_team])
            st.write("") 

    else:
        st.warning(f"The table '{table_to_query}' does not contain a 'matchup' column.")
        st.dataframe(all_data)

# -- Fallback message if data is empty for any selection
elif all_data.empty:
    st.info(f"Could not retrieve data for the selected league.")
