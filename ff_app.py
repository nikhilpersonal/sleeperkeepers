import streamlit as st
import pandas as pd
import numpy as np

# Load the CSV file containing ADPs from the local repository
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

# Function to convert ADP to draft round
def adp_to_round(adp, players_per_round):
    return int(np.ceil(adp / players_per_round))

# Function to provide insight based on ADP and keeper round
def evaluate_keeper_value(player_name, keeper_round, adp_data, column_name, players_per_round):
    player_data = adp_data[adp_data['Name'].str.lower() == player_name.lower()]
    
    if player_data.empty:
        return f"Player '{player_name}' not found in the ADP list."

    player_data = player_data.dropna(subset=[column_name])

    selected_adp = player_data.iloc[0][column_name]
    adp_round = adp_to_round(selected_adp, players_per_round)

    # Calculate the difference in rounds between the ADP round and the keeper round
    difference_rounds = keeper_round - adp_round

    # Set delta color based on the rounds difference
    if abs(difference_rounds) >= 4:
        delta_color = "normal"  # Green
    else:
        delta_color = "inverse"  # Red

    insight = f"Keeping {player_name} in round {keeper_round} is calculated with an ADP from {column_name}: {selected_adp:.1f}, which translates to round {adp_round}."

    # Display the metric, showing how many rounds off the keeper round is from the ADP round
    st.metric(label="Rounds Difference", value=f"{difference_rounds} rounds", delta=f"{abs(difference_rounds)} rounds", delta_color=delta_color)

    return insight

# Streamlit App
st.write("App is running...")

# Load the ADP data from the local file
adp_data = load_adp_data()

if adp_data is not None:
    st.write("ADP Data Preview:")
    st.dataframe(adp_data.head())

    players_per_round = st.number_input("Enter the number of players per round", min_value=1, value=10, step=1)
    player_name = st.selectbox("Select the player's name", adp_data['Name'].unique())
    column_name = st.selectbox("Select the source of ADP", ['Underdog', 'Sleeper', 'ESPN'])
    keeper_round = st.number_input("Enter the round in which you can keep the player", min_value=1, max_value=16, step=1)

    if st.button("Evaluate Keeper Value"):
        if player_name and keeper_round:
            insight = evaluate_keeper_value(player_name, keeper_round, adp_data, column_name, players_per_round)
            st.write(insight)
        else:
            st.write("Please enter both the player's name and the keeper round.")
else:
    st.write("Failed to load ADP data. Please check the file and format.")
