import json
from config import settings
from utils.logger import log

def save_to_file(data: dict, file_path: str):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

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

def merge_with_old_database(id_dict: dict, file_path: str) -> dict:
    json_data = load_from_file(file_path)
    for track_id, youtube_id in id_dict.items():
        json_data[track_id] = youtube_id
    return json_data