import json
from config import settings
from utils.logger import log

def save_to_file(data: dict, file_path: str):
    json_data = load_from_file(file_path)

    for spotify_id, youtube_id in data.items():
        if spotify_id in json_data:
            log(f"Skipping {spotify_id}, already cached.")
            continue
        else:
            json_data[spotify_id] = youtube_id

    with open(file_path, 'w') as file:
        json.dump(json_data, file, indent=4)

def load_from_file(file_path: str) -> dict:
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    
def substract_the_database_from(spotify_data: dict, file_path: str) -> dict:
    json_data = load_from_file(file_path)
    refined_spotify_data = []
    for track in spotify_data["tracks"]:
        if track['id'] in json_data:
            log(f"track {track['name']} with id {track['id']} found in database, it won't be searched.")
        else:
            log(f"track {track['name']} with id {track['id']} is a new entry!")
            refined_spotify_data.append(track)
    return refined_spotify_data