from enum import Enum
import os
import re
import requests
import yt_dlp
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, APIC, error

from utils.logger import log, BRIGHT_CYAN, BRIGHT_GREEN, BRIGHT_YELLOW, BRIGHT_MAGENTA, RESET
from utils.json_controller import save_to_file, substract_the_database_from, merge_with_old_database, load_from_file
from spotify.client import SpotifyClient
from youtube.client import get_video_ids
from config import settings

class PIPE_TAG(Enum):
    CACHE_PLAYLIST = 1
    DOWNLOAD_PLAYLIST = 2
    SYNC_ALL = 3

def run_pipeline(pipe_tag: PIPE_TAG, pl_id: str = ""):
    match pipe_tag:
        case PIPE_TAG.CACHE_PLAYLIST:
            cacher(pl_id)
        case PIPE_TAG.DOWNLOAD_PLAYLIST:
            downloader(pl_id)
        case PIPE_TAG.SYNC_ALL:
            sync_all()
        case _:
            log("Unknown pipe tag.")

def cacher(pl_id: str):
    sp = SpotifyClient()
    spotify_response_data = sp.get_pl_data(pl_id)
    log(f"playlist name: {spotify_response_data['playlist_name']}, track count: {spotify_response_data['track_count']}")
    log(f"the length of spotify_response_data[\"tracks\"] is {len(spotify_response_data['tracks'])}")
    refined_spotify_response_data = substract_the_database_from(spotify_response_data, settings.cache_path)
    log(f"logically 'OR'd the database and spotify_response_data (LEN:{len(refined_spotify_response_data)})")
    
    id_dict = get_video_ids(refined_spotify_response_data)
    log(f"id_dict (LEN:{len(id_dict)})")
    
    final_id_dict = merge_with_old_database(id_dict, settings.cache_path)
    log(f"final_id_dict (LEN:{len(final_id_dict)})")
    save_to_file(final_id_dict, settings.cache_path)

def downloader(pl_id: str):
    # Ensure cache is up to date first
    cacher(pl_id)
    
    sp = SpotifyClient()
    pl_data = sp.get_pl_data(pl_id)
    cache = load_from_file(settings.cache_path)
    
    pl_name_safe = re.sub(r'[<>:"/\\|.?*]', "", pl_data['playlist_name'])
    save_dir = os.path.join(settings.save_dir or "downloads", pl_name_safe)
    os.makedirs(save_dir, exist_ok=True)
    
    # Store ID metadata to power future sync operations
    with open(os.path.join(save_dir, ".sync_id"), "w") as f:
        f.write(pl_id)
    
    valid_mp3_files = set()
    
    total = len(pl_data['tracks'])
    for i, track in enumerate(pl_data['tracks'], 1):
        video_id = cache.get(track['id'])
        if not video_id:
            log(f"Warning: {track['name']} not found in cache. Skipping.")
            continue
            
        video_url = f"https://music.youtube.com/watch?v={video_id}"
        track_name_safe = re.sub(r'[\\/*?:"<>|.İ]', "", f"{track['artist_name']} - {track['name']}")
        mp3_name = f"{track_name_safe}.mp3"
        mp3_path = os.path.join(save_dir, mp3_name)
        valid_mp3_files.add(mp3_name)
        
        if os.path.exists(mp3_path):
            log(f"{BRIGHT_YELLOW}[{i}/{total}] Already downloaded:{RESET} {track_name_safe}.mp3")
            continue
            
        log(f"{BRIGHT_CYAN}[{i}/{total}] Extracting Audio:{RESET} {track['name']} - {track['artist_name']}")
        ydl_opts = {
            'format': 'ba/bestaudio/best',
            'outtmpl': os.path.join(save_dir, f"{track_name_safe}.%(ext)s"),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
            'no_warnings': True
        }
        
        cookie_path = os.path.join(settings.save_dir or "data", "cookies.txt")
        if os.path.exists("data/cookies.txt"):
            ydl_opts['cookiefile'] = "data/cookies.txt"
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
        except Exception as e:
            log(f"Failed to download {video_url}: {e}")
            continue
            
        try:
            audio = MP3(mp3_path, ID3=ID3)
            try:
                audio.add_tags()
            except error:
                pass
            
            audio.tags["TIT2"] = TIT2(encoding=3, text=track['name'])
            audio.tags["TPE1"] = TPE1(encoding=3, text=track['artist_name'])
            
            if track.get('album_name'):
                audio.tags["TALB"] = TALB(encoding=3, text=track['album_name'])
            
            if track.get('cover_url'):
                try:
                    img_response = requests.get(track['cover_url'], timeout=10)
                    img_response.raise_for_status()
                    audio.tags["APIC"] = APIC(
                        encoding=3,
                        mime="image/jpeg",
                        type=3,
                        desc="Cover",
                        data=img_response.content
                    )
                except Exception as img_e:
                    log(f"Failed to fetch cover art for {track['name']}: {img_e}")
                    
            audio.save()
            log(f"{BRIGHT_GREEN}[{i}/{total}] Successfully tagged:{RESET} {track_name_safe}.mp3")
        except Exception as tag_e:
            log(f"Failed to tag {mp3_path}: {tag_e}")

    # --- Synchronization / Cleanup Phase ---
    log(f"{BRIGHT_CYAN}Syncing local directory... Checking for deleted tracks.{RESET}")
    for existing_file in os.listdir(save_dir):
        if existing_file.endswith(".mp3") and existing_file not in valid_mp3_files:
            file_path = os.path.join(save_dir, existing_file)
            try:
                os.remove(file_path)
                log(f"{BRIGHT_YELLOW}Deleted removed track:{RESET} {existing_file}")
            except Exception as e:
                log(f"Failed to delete {existing_file}: {e}")

def sync_all():
    base_dir = settings.save_dir or "downloads"
    if not os.path.exists(base_dir):
        log(f"{BRIGHT_YELLOW}No downloads directory found to sync.{RESET}")
        return
        
    for folder_name in os.listdir(base_dir):
        folder_path = os.path.join(base_dir, folder_name)
        sync_file = os.path.join(folder_path, ".sync_id")
        if os.path.isdir(folder_path) and os.path.exists(sync_file):
            with open(sync_file, "r") as f:
                pl_id = f.read().strip()
            if pl_id:
                log(f"{BRIGHT_MAGENTA}=== Syncing Previously Downloaded Playlist: {folder_name} ==={RESET}")
                try:
                    downloader(pl_id)
                    log(f"{BRIGHT_GREEN}=== Finished Syncing: {folder_name} ==={RESET}\n")
                except Exception as e:
                    log(f"{BRIGHT_YELLOW}=== Failed to sync {folder_name}: {e} ==={RESET}\n")
