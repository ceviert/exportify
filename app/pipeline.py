from enum import Enum
import os
from utils.logger import log
from utils.json_controller import save_to_file, substract_the_database_from
from spotify.client import SpotifyClient
from youtube.client import get_video_ids
from config import settings

class PIPE_TAG(Enum):
    CACHE_PLAYLIST = 1
    DOWNLOAD_PLAYLIST = 2

def run_pipeline(pipe_tag: PIPE_TAG, pl_id: str):
    match pipe_tag:
        case PIPE_TAG.CACHE_PLAYLIST:
            cacher(pl_id)
        case PIPE_TAG.DOWNLOAD_PLAYLIST:
            downloader(pl_id)
        case _:
            log("Unknown pipe tag.")

def cacher(pl_id: str):
    sp = SpotifyClient()
    spotify_response_data = sp.get_pl_data(pl_id)
    log(f"playlist name: {spotify_response_data["playlist_name"]}, track count: {spotify_response_data["track_count"]}")
    log(f"{spotify_response_data}")
    log(f"the length of spotify_response_data[\"tracks\"] is {len(spotify_response_data["tracks"])}")
    refined_spotify_response_data = substract_the_database_from(spotify_response_data, settings.cache_path)
    log("logically 'OR'd the database and spotify_response_data")
    id_dict = get_video_ids(refined_spotify_response_data)
    save_to_file(id_dict, settings.cache_path)