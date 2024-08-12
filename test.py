import os
import streamlit as st
import pandas as pd
import requests

# Path to the CSV file for storing drafts
drafts_csv = "saved_drafts.csv"

# Function to load saved drafts
def load_saved_drafts():
    if os.path.exists(drafts_csv):
        return pd.read_csv(drafts_csv)
    else:
        return pd.DataFrame(columns=["name", "league_id", "draft_id"])

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
    # Convert player name to filename format
    filename = f"{player_name.replace(' ', '_')}.png"
    image_path = os.path.join('player_images', filename)
    
    # Check if the file exists
    if os.path.exists(image_path):
        return image_path
    return None

# Streamlit app UI
st.title("Sleeper Draft Results")

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

    # Session state to hold draft data to prevent reloading
    if 'draft_data' not in st.session_state:
        st.session_state.draft_data = None
        st.session_state.team_id_to_name = None

    if st.button("Fetch Draft Results"):
        # Fetch rosters to map team IDs to names
        rosters = fetch_league_rosters(league_id)
        team_id_to_name = map_team_id_to_name(rosters)
        
        # Fetch draft picks
        draft_picks = fetch_draft_picks(draft_id)
        
        if draft_picks:
            # Extract and clean up relevant information
            clean_data = []
            for pick in draft_picks:
                player_name = f"{pick['metadata'].get('first_name', '')} {pick['metadata'].get('last_name', '')}"
                image_path = check_player_image_exists(player_name)
                clean_data.append({
                    'team_name': team_id_to_name.get(pick['roster_id'], "Unknown Team"),
                    'full_name': player_name,
                    'position': pick['metadata'].get('position', 'Unknown'),
                    'round': pick['round'],
                    'pick_no': pick['pick_no'],
                    'is_keeper_info': pick.get('is_keeper', 'No'),  # Safely get 'is_keeper' info
                    'image_path': image_path  # Path to the player's image if it exists
                })
            
            # Convert to DataFrame for easier display
            clean_df = pd.DataFrame(clean_data)

            # Store data in session state
            st.session_state.draft_data = clean_df
            st.session_state.team_id_to_name = team_id_to_name

    # Check if draft data is available in session state
    if st.session_state.draft_data is not None:
        clean_df = st.session_state.draft_data
        
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
                col1, col2 = st.columns([1, 4])
                
                with col1:
                    if image_path:
                        st.image(image_path, width=90)  # Larger image size

                with col2:
                    st.markdown(f"""
                    <div style="border:2px solid #ddd; padding:15px; border-radius:10px; background-color:#f9f9f9;">
                        <strong style="font-size: 1.25em;">{row['full_name']}</strong> - {row['position']}<br>
                        <small style="font-size: 1.1em;">Round {row['round']}, Pick {row['pick_no']}</small>
                    </div>
                    """, unsafe_allow_html=True)
