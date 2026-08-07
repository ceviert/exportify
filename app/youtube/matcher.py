"""Pure, dependency-free helpers for matching Spotify tracks to YouTube Music results."""

DURATION_MARGIN_SECONDS = 15


def to_query(track_info: dict) -> str:
    track_name = track_info["name"]
    track_artist = track_info["artist_name"]
    return f"{track_name} - {track_artist}"


def match_reason(track: dict, result: dict):
    """Return a human-readable reason this result is rejected, or None if acceptable.

    The string is meant for diagnostics/logging, so include the measured values
    (e.g. the duration delta) rather than a bare "rejected".
    """
    if not isinstance(result, dict):
        return "result is not a dict"
    category = result.get("category")
    if category not in ("Songs", "Top result", None):
        return f"category '{category}' (not Songs/Top result)"
    if result.get("resultType") not in ("song", "video"):
        return f"type '{result.get('resultType')}' (not song/video)"

    spotify_title = track["name"].lower()
    youtube_title = result.get("title", "").lower()

    # Skip live versions unless the Spotify track itself is live
    if "live" not in spotify_title and "live" in youtube_title:
        return "it's a live version"

    # Skip full-album uploads unless the Spotify title mentions an album
    if "album" not in spotify_title and "album" in youtube_title:
        return "it's a full-album upload"

    # Skip significantly different durations (15-second margin)
    sp_dur_ms = track.get("duration_ms", 0)
    yt_dur_sec = result.get("duration_seconds", 0)
    if sp_dur_ms > 0 and yt_dur_sec > 0:
        sp_dur_sec = sp_dur_ms / 1000
        delta = abs(sp_dur_sec - yt_dur_sec)
        if delta > DURATION_MARGIN_SECONDS:
            return f"duration mismatch ({delta:.0f}s off: Spotify {sp_dur_sec:.0f}s vs YT {yt_dur_sec:.0f}s)"

    return None


def is_acceptable_match(track: dict, result: dict) -> bool:
    """Return True if a YouTube Music search result is an acceptable match for a Spotify track."""
    return match_reason(track, result) is None


def choose_song_match(track: dict, results: list):
    """Pick the best YouTube Music song result for a Spotify track.

    Returns (result, is_fallback, rejected) where:
    - result is the chosen result dict, or None if nothing was acceptable
    - is_fallback is True when result only passed by relaxing the duration gate
    - rejected is a list of (result, reason) for every result that wasn't chosen

    Strategy:
    1. Prefer the first result that passes all gates (relevance order).
    2. If none pass, fall back to the result that passes every gate except the
       duration one, choosing the one with the smallest duration difference.
    """
    sp_dur_sec = (track.get("duration_ms") or 0) / 1000

    rejected = []
    for result in results:
        reason = match_reason(track, result)
        if reason is None:
            return result, False, rejected
        rejected.append((result, reason))

    # Fallback: closest duration among results rejected only for duration.
    best = None
    best_delta = None
    for result, reason in rejected:
        if not reason.startswith("duration mismatch"):
            continue
        delta = abs(sp_dur_sec - (result.get("duration_seconds") or 0))
        if best_delta is None or delta < best_delta:
            best, best_delta = result, delta

    return best, best is not None, rejected


def candidate_results(track: dict, results: list, exclude_ids=None) -> list:
    """Return acceptable search results in priority order, skipping tried ids.

    Fully-gated matches come first (in search order), then duration-fallback
    candidates ordered by closeness to the Spotify duration. Used to offer an
    alternative when the primary video fails to download (e.g. an age-gated
    upload), so the caller never re-offers an id that already failed.
    """
    exclude = set(exclude_ids or [])
    good, fallback = [], []

    for result in results:
        if not isinstance(result, dict) or not result.get("videoId"):
            continue
        if result["videoId"] in exclude:
            continue
        reason = match_reason(track, result)
        if reason is None:
            good.append(result)
        elif reason.startswith("duration mismatch"):
            fallback.append(result)

    sp_dur_sec = (track.get("duration_ms") or 0) / 1000
    fallback.sort(key=lambda r: abs(sp_dur_sec - (r.get("duration_seconds") or 0)))
    return good + fallback
