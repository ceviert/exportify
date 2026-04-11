import argparse
from pipeline import PIPE_TAG, run_pipeline

def extract_playlist_id(playlist_str: str) -> str:
    # If the user passed a full URL, e.g., https://open.spotify.com/playlist/0bFXt3PTlM32bRKGO6zh7p?si=123
    if "spotify.com/playlist/" in playlist_str:
        return playlist_str.split("spotify.com/playlist/")[1].split("?")[0]
    return playlist_str

def main():
    parser = argparse.ArgumentParser(description="Exportify: Spotify to YouTube MP3 Downloader")
    parser.add_argument(
        '--action',
        type=str,
        choices=['cache', 'download', 'sync'],
        required=True,
        help='Whether to cache, download, or sync previously downloaded playlists.'
    )
    parser.add_argument(
        '--playlist',
        nargs='*',
        type=str,
        required=False,
        help='One or more Spotify playlist IDs or full URLs.'
    )
    
    args = parser.parse_args()
    
    if args.action == 'sync':
        run_pipeline(PIPE_TAG.SYNC_ALL, "")
        return
        
    if not args.playlist:
        print("Error: --playlist is required for 'cache' or 'download' actions.")
        return
    
    for playlist_arg in args.playlist:
        pl_id = extract_playlist_id(playlist_arg)
        
        if args.action == 'cache':
            run_pipeline(PIPE_TAG.CACHE_PLAYLIST, pl_id)
        elif args.action == 'download':
            run_pipeline(PIPE_TAG.DOWNLOAD_PLAYLIST, pl_id)

if __name__ == "__main__":
    main()