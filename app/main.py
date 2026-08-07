import argparse
from pipeline import PIPE_TAG, run_pipeline
from utils.urls import extract_playlist_id

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
    parser.add_argument(
        '--no-refresh-cache',
        action='store_true',
        help='Skip refreshing the song cache before downloading. Only use if the cache is already up to date.'
    )

    args = parser.parse_args()
    refresh_cache = not args.no_refresh_cache
    
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
            run_pipeline(PIPE_TAG.DOWNLOAD_PLAYLIST, pl_id, refresh_cache=refresh_cache)

if __name__ == "__main__":
    main()