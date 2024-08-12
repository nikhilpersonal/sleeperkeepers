import streamlit as st
import pandas as pd

# Load the data
@st.cache_data
def load_data():
    df = pd.read_csv('data.csv')
    df['ADP'] = df['Underdog']  # Using 'Underdog' as ADP
    return df

df = load_data()

# Streamlit app
st.title('Fantasy Football ADP Comparison')

# User input
player_name = st.text_input('Enter player name:')
round_number = st.number_input('Enter round number:', min_value=1, max_value=20, value=1)

# Calculate pick number
picks_per_round = 12  # Assuming a 12-team league
pick_number = (round_number - 1) * picks_per_round + 1

if player_name:
    # Find the player in the dataframe
    player = df[df['Name'].str.lower() == player_name.lower()]
    
    if not player.empty:
        adp = player['ADP'].values[0]
        
        st.write(f"Player: {player['Name'].values[0]}")
        st.write(f"Position: {player['Pos'].values[0]}")
        st.write(f"Team: {player['Team'].values[0]}")
        st.write(f"ADP: {adp:.2f}")
        st.write(f"Your pick: Round {round_number}, Pick {pick_number}")
        
        if adp < pick_number:
            st.success(f"Good value! {player['Name'].values[0]} is typically drafted {pick_number - adp:.0f} picks earlier.")
        elif adp > pick_number:
            st.warning(f"Reaching a bit. {player['Name'].values[0]} is typically drafted {adp - pick_number:.0f} picks later.")
        else:
            st.info(f"Right on target! {player['Name'].values[0]} is typically drafted at this position.")
    else:
        st.error("Player not found. Please check the spelling and try again.")
