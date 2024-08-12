import requests
from bs4 import BeautifulSoup
import re

def get_espn_player_id(player_name):
    # Replace spaces with %20 for URL encoding
    search_query = player_name.replace(" ", "%20")
    
    # Construct the search URL on ESPN
    search_url = f"https://www.espn.com/search/results?q={search_query}&page=1&content=players"
    
    # Make a request to the ESPN search page
    response = requests.get(search_url)
    if response.status_code != 200:
        print(f"Could not retrieve search results for {player_name}. HTTP Status Code: {response.status_code}")
        return None

    # Parse the HTML content
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find the first player link in the search results
    player_link = None
    for link in soup.find_all('a', href=True):
        href = link['href']
        # Look for a URL that matches the player profile pattern
        if re.search(r'/player/_/id/\d+', href):
            player_link = href
            break
    
    if not player_link:
        print(f"Could not find ESPN profile for {player_name}")
        return None
    
    # Extract the player ID from the URL
    player_id_match = re.search(r'/player/_/id/(\d+)', player_link)
    if player_id_match:
        player_id = player_id_match.group(1)
        print(f"Found ESPN ID for {player_name}: {player_id}")
        return player_id
    else:
        print(f"Could not extract player ID for {player_name}")
        return None

def get_player_ids(player_names):
    player_ids = {}
    for player_name in player_names:
        player_id = get_espn_player_id(player_name)
        if player_id:
            player_ids[player_name] = player_id
    return player_ids

# Example usage
player_names = ["Patrick Mahomes", "Josh Allen", "Aaron Donald"]
player_ids = get_player_ids(player_names)

# Print the results
for name, player_id in player_ids.items():
    print(f"Player: {name}, ESPN ID: {player_id}")
