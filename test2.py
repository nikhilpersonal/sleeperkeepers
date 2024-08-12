import os
import requests
import streamlit as st
import pandas as pd
import numpy as np

# Path to the CSV file for storing drafts
drafts_csv = "saved_drafts.csv"

# Function to load saved drafts
def load_saved_drafts():
    if os.path.exists(drafts_csv):
        return pd.read_csv(drafts_csv)
    else:
        return pd.DataFrame(columns(["name", "league_id", "draft_id"]))

# Function to save a new draft
def save_new_draft(name, league_id, draft_id):
    new_draft = pd.DataFrame({
        "name": [name],
        "league_id": [league_id],
        "draft_id": [draft_id]
    })
    if os.path.exists(drafts_csv):
        existing_drafts = pd.read_csv(drafts_csv)
        updated_drafts = pd.concat([existing_drafts, new_draft], ignore_index=True)
    else:
        updated_drafts = new_draft
    updated_drafts.to_csv(drafts_csv, index=False)

# Function to fetch draft picks for a given draft ID
def fetch_draft_picks(draft_id):
    draft_picks_url = f"https://api.sleeper.app/v1/draft/{draft_id}/picks"
    picks_response = requests.get(draft_picks_url)
    return picks_response.json()

# Function to fetch league rosters to get team names
def fetch_league_rosters(league_id):
    rosters_url = f"https://api.sleeper.app/v1/league/{league_id}/rosters"
    rosters_response = requests.get(rosters_url)
    return rosters_response.json()

# Function to fetch user details by owner ID
def fetch_user_details(user_id):
    user_url = f"https://api.sleeper.app/v1/user/{user_id}"
    user_response = requests.get(user_url)
    return user_response.json()

# Function to map team_id to team name
def map_team_id_to_name(rosters):
    team_id_to_name = {}
    for roster in rosters:
        team_id = roster['roster_id']
        owner_id = roster['owner_id']
        user_details = fetch_user_details(owner_id)
        team_name = user_details.get('display_name', f"Team {team_id}")  # Default to "Team {id}" if no name
        team_id_to_name[team_id] = team_name
    return team_id_to_name

# Function to check if player image exists
def check_player_image_exists(player_name):
    filename = f"{player_name.replace(' ', '_')}.png"
    image_path = os.path.join('player_images', filename)
    if os.path.exists(image_path):
        return image_path
    return None

# Load the ADP data
@st.cache_data
def load_adp_data():
    try:
        data = pd.read_csv('data.csv')
        data.rename(columns={'Sleeper.1': 'ESPN'}, inplace=True)
        data[['Underdog', 'Sleeper', 'ESPN']] = data[['Underdog', 'Sleeper', 'ESPN']].apply(pd.to_numeric, errors='coerce')
        return data
    except Exception as e:
        st.write("Error loading data:", e)
        return None

# Convert ADP to draft round
def adp_to_round(adp, players_per_round):
    if pd.isna(adp):
        return None
    return int(np.ceil(adp / players_per_round))

# Evaluate keeper value based on ADP and keeper round
def evaluate_keeper_value(player_name, keeper_round, adp_data, column_name, players_per_round):
    player_data = adp_data[adp_data['Name'].str.lower() == player_name.lower()]
    
    if player_data.empty:
        return f"Player '{player_name}' not found in the ADP list."

    player_data = player_data.dropna(subset=[column_name])

    if player_data.empty:
        return f"ADP data for {player_name} is not available."

    selected_adp = player_data.iloc[0][column_name]
    adp_round = adp_to_round(selected_adp, players_per_round)

    if adp_round is None:
        return f"ADP data for {player_name} is not available."

    difference_rounds = adp_round - keeper_round

    # Determine delta color based on the difference in rounds
    if difference_rounds < 0:
        delta_color = "inverse"  # Green for good value
    else:
        delta_color = "inverse"  # Red for bad value

    insight = f"Keeping {player_name} in round {keeper_round} is calculated with an ADP from {column_name}: {selected_adp:.1f}, which translates to round {adp_round}."

    # Display the metric
    st.metric(label=f"{player_name} (ADP: {selected_adp:.1f})", value=f"{difference_rounds} rounds", delta=f"{difference_rounds} rounds", delta_color=delta_color)

    return insight

# Streamlit app UI
st.title("Sleeper Draft Results with ADP Analysis")

# Load saved drafts
saved_drafts = load_saved_drafts()

# Dropdown to select saved draft or option to add a new draft
draft_options = ["Add a new draft"] + saved_drafts["name"].tolist()
selected_draft = st.selectbox("Select a saved draft or add a new one:", draft_options)

# If the user selects to add a new draft
if selected_draft == "Add a new draft":
    draft_name = st.text_input("Enter a name for the draft:")
    league_id = st.text_input("Enter the League ID:")
    draft_id = st.text_input("Enter the Draft ID:")

    if st.button("Save Draft"):
        if draft_name and league_id and draft_id:
            save_new_draft(draft_name, league_id, draft_id)
            st.success(f"Draft '{draft_name}' saved successfully!")
            st.experimental_rerun()  # Reload the app to update the saved drafts list
        else:
            st.error("Please fill out all fields.")
else:
    # Load the selected draft details
    selected_row = saved_drafts[saved_drafts["name"] == selected_draft]
    league_id = selected_row["league_id"].values[0]
    draft_id = selected_row["draft_id"].values[0]

    # Load the ADP data
    adp_data = load_adp_data()

    # Dropdown to select the ADP source column
    adp_columns = ["Sleeper", "Underdog", "ESPN"]  # Default columns; this list can be expanded
    selected_adp_column = st.selectbox("Select the ADP source:", adp_columns, index=0)

    # Session state to hold draft data to prevent reloading
    if 'draft_data' not in st.session_state:
        st.session_state.draft_data = None
        st.session_state.team_id_to_name = None
        st.session_state.players_per_round = None

    if st.button("Fetch Draft Results"):
        # Fetch rosters to map team IDs to names
        rosters = fetch_league_rosters(league_id)
        team_id_to_name = map_team_id_to_name(rosters)
        
        # Fetch draft picks
        draft_picks = fetch_draft_picks(draft_id)
        
        if draft_picks:
            # Calculate the number of players per round based on roster size
            num_teams = len(rosters)
            rounds = max(int(pick['round']) for pick in draft_picks)
            players_per_round = num_teams
            
            # Save in session state
            st.session_state.players_per_round = players_per_round
            
            # Extract and clean up relevant information
            clean_data = []
            for pick in draft_picks:
                player_name = f"{pick['metadata'].get('first_name', '')} {pick['metadata'].get('last_name', '')}"
                image_path = check_player_image_exists(player_name)
                
                # Find the ADP for the player
                adp_row = adp_data[adp_data["Name"].str.lower() == player_name.lower()]
                
                if not adp_row.empty:
                    adp_value = adp_row[selected_adp_column].values[0]
                    adp_round = adp_to_round(adp_value, players_per_round)
                    round_diff = adp_round - pick['round'] if adp_round is not None else None
                else:
                    adp_value = None
                    round_diff = None
                
                clean_data.append({
                    'team_name': team_id_to_name.get(pick['roster_id'], "Unknown Team"),
                    'full_name': player_name,
                    'position': pick['metadata'].get('position', 'Unknown'),
                    'round': pick['round'],
                    'pick_no': pick['pick_no'],
                    'is_keeper_info': pick.get('is_keeper', 'No'),
                    'image_path': image_path,
                    'round_diff': round_diff  # Add round differential to the data
                })
            
            # Convert to DataFrame for easier display
            clean_df = pd.DataFrame(clean_data)

            # Store data in session state
            st.session_state.draft_data = clean_df
            st.session_state.team_id_to_name = team_id_to_name

    # Check if draft data is available in session state
    if st.session_state.draft_data is not None:
        clean_df = st.session_state.draft_data
        players_per_round = st.session_state.players_per_round
        
        # Hide full draft data under a dropdown
        with st.expander("Show Full Draft Data"):
            st.write("Full Draft Data:")
            st.dataframe(clean_df)
        
        # Dropdown to select a team
        selected_team = st.selectbox("Select a Team Name:", clean_df['team_name'].unique(), key="team_select")
        
        if selected_team:
            # Filter data for the selected team
            team_picks = clean_df[clean_df['team_name'] == selected_team]
            
            # Display relevant information in a clean format
            st.write(f"Draft Picks for {selected_team}:")
            for index, row in team_picks.iterrows():
                image_path = row['image_path']
                
                # Use a horizontal layout with st.image and st.markdown
                col1, col2, col3 = st.columns([1, 4, 2])
                
                with col1:
                    if image_path:
                        st.image(image_path, width=90)

                with col2:
                    st.markdown(f"""
                    <div style="border:2px solid #ddd; padding:15px; border-radius:10px; background-color:#f9f9f9;">
                        <strong style="font-size: 1.25em;">{row['full_name']}</strong> - {row['position']}<br>
                        <small style="font-size: 1.1em;">Round {row['round']}, Pick {row['pick_no']}</small>
                    </div>
                    """, unsafe_allow_html=True)

                with col3:
                    if row['round_diff'] is not None:
                        evaluate_keeper_value(row['full_name'], row['round'], adp_data, selected_adp_column, players_per_round)
                    else:
                        st.write("ADP not available")
