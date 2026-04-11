import ytmusicapi
from utils.json_controller import load_from_file
from utils.logger import log, BRIGHT_CYAN, BRIGHT_MAGENTA, BRIGHT_GREEN, RESET

def to_query(track_info: dict) -> str:
    track_name = track_info["name"]
    track_artist = track_info["artist_name"]
    return f"{track_name} - {track_artist}"

def get_video_ids(spotify_data: dict) -> dict:
    log(f"Starting YouTube Music search for {len(spotify_data)} new tracks...")
    ytm = ytmusicapi.YTMusic()
    sp_yt_dict = {}
    total = len(spotify_data)

    for i, track in enumerate(spotify_data, 1):
        query = to_query(track)
        log(f"{BRIGHT_CYAN}Search [{i}/{total}]{RESET} for: {BRIGHT_MAGENTA}'{query}'{RESET}")
        search_results = ytm.search(query)
        for result in search_results:
            if isinstance(result, dict) and 'resultType' in result and result['category'] in ['Songs', 'Top result', None] and result['resultType'] in ['song', 'video']:
                # Filter out live versions if the original track is not live
                spotify_title = track["name"].lower()
                youtube_title = result.get("title", "").lower()
                if "live" not in spotify_title and "live" in youtube_title:
                    log(f"Skipping '{result['title']}' because the Spotify track is not a live version.")
                    continue

                # Filter out full albums if the original track doesn't contain album
                if "album" not in spotify_title and "album" in youtube_title:
                    log(f"Skipping '{result['title']}' because it appears to be a full album.")
                    continue
                    
                # Filter out significantly different durations (15 seconds margin)
                sp_dur_ms = track.get("duration_ms", 0)
                yt_dur_sec = result.get("duration_seconds", 0)
                if sp_dur_ms > 0 and yt_dur_sec > 0:
                    sp_dur_sec = sp_dur_ms / 1000
                    if abs(sp_dur_sec - yt_dur_sec) > 15:
                        log(f"Skipping '{result['title']}' due to duration difference: {abs(sp_dur_sec - yt_dur_sec):.1f}s.")
                        continue

                log(f"{BRIGHT_GREEN}Matched!{RESET} [{track['name']}] => {result['title']}")
                log(f"URL: https://www.youtube.com/watch?v={result['videoId']}")
                sp_yt_dict[track["id"]] = result['videoId']
                log("-----------------------------------------------------------")
                break

    return sp_yt_dict