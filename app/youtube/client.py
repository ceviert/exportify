from collections import Counter

import ytmusicapi

from utils.logger import log, BRIGHT_CYAN, BRIGHT_MAGENTA, BRIGHT_GREEN, BRIGHT_YELLOW, RESET
from youtube.matcher import to_query, choose_song_match, candidate_results


def get_video_ids(spotify_data: dict) -> dict:
    log(f"Starting YouTube Music search for {len(spotify_data)} new tracks...")
    ytm = ytmusicapi.YTMusic()
    sp_yt_dict = {}
    total = len(spotify_data)

    for i, track in enumerate(spotify_data, 1):
        query = to_query(track)
        log(f"{BRIGHT_CYAN}Search [{i}/{total}]{RESET} for: {BRIGHT_MAGENTA}'{query}'{RESET}")

        # Only results YouTube Music itself classifies as songs.
        search_results = ytm.search(query, filter="songs")
        result, is_fallback, rejected = choose_song_match(track, search_results)

        if result is None:
            if rejected:
                counts = Counter(reason for _, reason in rejected)
                summary = ", ".join(f"{count}x {reason}" for reason, count in counts.most_common())
                log(f"{BRIGHT_YELLOW}No acceptable match found for '{query}'.{RESET} Skipped {len(rejected)} result(s): {summary}.")
            else:
                log(f"{BRIGHT_YELLOW}No acceptable match found for '{query}'.{RESET} No song results returned.")
            continue

        fallback_note = " (duration fallback)" if is_fallback else ""
        log(f"{BRIGHT_GREEN}Matched!{RESET} [{track['name']}] => {result['title']}{fallback_note}")
        log(f"URL: https://www.youtube.com/watch?v={result['videoId']}")
        sp_yt_dict[track["id"]] = result['videoId']
        log("-----------------------------------------------------------")

    return sp_yt_dict


def find_alternative_results(track: dict, exclude_ids=None) -> list:
    """Search YouTube Music for a track and return acceptable candidates.

    Candidates are ordered by priority (fully-gated first, then closest
    duration-fallback), with any already-tried video ids excluded. Used to offer
    an alternative when the cached match fails to download.
    """
    ytm = ytmusicapi.YTMusic()
    query = to_query(track)
    results = ytm.search(query, filter="songs")
    return candidate_results(track, results, exclude_ids=exclude_ids)
