import streamlit as st
import requests
import pandas as pd
import urllib.parse
from bs4 import BeautifulSoup

import urllib.parse
import requests
from bs4 import BeautifulSoup

def get_player_headshot(player_name):
    try:
        # Encode the player name for use in URL
        encoded_name = urllib.parse.quote(player_name)
        
        # NFL.com search URL
        search_url = f"https://www.nfl.com/players/search?name={encoded_name}"
        print(f"Searching URL: {search_url}")
        
        # Send a GET request to the search URL
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(search_url, headers=headers)
        print(f"Search page status code: {response.status_code}")
        
        # Print the first 1000 characters of the response content
        print("First 1000 characters of the response:")
        print(response.text[:1000])
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the first player link
        player_link = soup.find('a', class_='d3-o-player-fullname')
        
        if player_link:
            # Get the player's individual page URL
            player_url = f"https://www.nfl.com{player_link['href']}"
            print(f"Player page URL: {player_url}")
            
            # Send a GET request to the player's page
            player_response = requests.get(player_url, headers=headers)
            print(f"Player page status code: {player_response.status_code}")
            
            player_soup = BeautifulSoup(player_response.content, 'html.parser')
            
            # Find the player's headshot image
            headshot = player_soup.find('img', class_='d3-o-player-headshot')
            
            if headshot and 'src' in headshot.attrs:
                return headshot['src']
            else:
                print("Couldn't find headshot image on player's page")
        else:
            print("Couldn't find player link on search page")
        
        # Print all links found on the page
        print("\nAll links found on the page:")
        for link in soup.find_all('a'):
            print(link.get('href'))
    
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    
    return None



player_name = "Patrick Mahomes"
headshot_url = get_player_headshot(player_name)

if headshot_url:
    st.write(f"Headshot URL for {player_name}: {headshot_url}")
else:
    st.write(f"Couldn't find a headshot for {player_name}")