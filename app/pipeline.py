from enum import Enum
import os
from utils.logger import log
from utils.json_controller import save_to_file
from spotify.client import SpotifyClient
from youtube.client import get_video_ids

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
    spotify_data = sp.get_pl_items(pl_id)
    get_video_ids(spotify_data)