import csv
import requests
from PIL import Image
from io import BytesIO

def get_espn_player_headshot(player_id, player_name):
    # Construct the ESPN API URL
    url = f"https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/athletes/{player_id}"
    
    # Make the API request
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Could not retrieve profile for {player_name}. HTTP Status Code: {response.status_code}")
        return
    
    # Parse the JSON response
    player_data = response.json()
    
    # Extract the headshot URL
    img_url = player_data.get('headshot', {}).get('href')
    
    if not img_url:
        print(f"Could not find headshot for {player_name}")
        return
    
    # Download the image
    img_response = requests.get(img_url)
    if img_response.status_code != 200:
        print(f"Could not retrieve headshot image for {player_name}. HTTP Status Code: {img_response.status_code}")
        return
    
    # Open the image with PIL
    img = Image.open(BytesIO(img_response.content))
    
    # Save the image as a PNG file
    save_path = f"{player_name.replace(' ', '_').lower()}.png"
    img.save(save_path, format='PNG')
    
    print(f"Saved headshot for {player_name} as {save_path}")

def download_images_from_csv(csv_file):
    with open(csv_file, mode='r') as file:
        reader = csv.reader(file)
        for row in reader:
            if len(row) != 2:
                print(f"Skipping invalid row: {row}")
                continue
            player_name, player_id = row
            get_espn_player_headshot(player_id, player_name)

# Example usage
csv_file = 'playerid.csv'  # Specify the path to your CSV file
download_images_from_csv(csv_file)
