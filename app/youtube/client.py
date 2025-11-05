import ytmusicapi
from utils.json_controller import load_from_file
from utils.logger import log

def to_query(track_info: dict) -> str:
    track_name = track_info["name"]
    track_artist = track_info["artist_name"]
    return f"{track_name} - {track_artist}"

def get_video_ids(spotify_data: dict) -> dict:
    log(f"starting search with the spotify data: {spotify_data}")
    ytm = ytmusicapi.YTMusic()
    sp_yt_dict = {}

    for track in spotify_data:
        query = to_query(track)
        search_results = ytm.search(query)
        for result in search_results:
            if isinstance(result, dict) and 'resultType' in result and result['resultType'] == 'song' and result['category'] in ['Songs', 'Top result']:
                log(f"the query {query} brought back a result with the title {result['title']}, by {result['artists'][0]['name']} - https://www.youtube.com/watch?v={result['videoId']}")
                sp_yt_dict[track["id"]] = result['videoId']
                log(f"matched {track["id"]} with {result['videoId']}")
                log("-----------------------------------------------------------")

    return sp_yt_dict