import json
from config import settings
from utils.logger import log

def save_to_file(data: dict, file_path: str):
    json_data = load_from_file(file_path)

    for spotify_id, youtube_id in data.items():
        if spotify_id in json_data:
            log(f"Skipping {spotify_id}, already cached.")
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