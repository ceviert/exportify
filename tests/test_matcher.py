from youtube.matcher import is_acceptable_match, match_reason, choose_song_match, to_query


def track(**overrides):
    base = {
        "id": "t1",
        "name": "Man in the Box",
        "artist_name": "Alice In Chains",
        "album_name": "Facelift",
        "duration_ms": 268000,
    }
    base.update(overrides)
    return base


def yt_result(**overrides):
    base = {
        "category": "Songs",
        "resultType": "song",
        "title": "Man in the Box",
        "videoId": "v1",
        "duration_seconds": 268,
    }
    base.update(overrides)
    return base


# --- is_acceptable_match (boolean wrapper) ---

def test_accepts_good_match():
    assert is_acceptable_match(track(), yt_result()) is True


def test_rejects_non_dict_result():
    assert is_acceptable_match(track(), "not a dict") is False


def test_rejects_wrong_category():
    assert is_acceptable_match(track(), yt_result(category="Videos")) is False


def test_rejects_wrong_result_type():
    assert is_acceptable_match(track(), yt_result(resultType="playlist")) is False


def test_rejects_live_version_when_original_is_not_live():
    assert is_acceptable_match(track(), yt_result(title="Man in the Box (Live)")) is False


def test_accepts_live_version_when_original_is_live():
    assert is_acceptable_match(track(name="Man in the Box (Live)"), yt_result(title="Man in the Box (Live)")) is True


def test_rejects_full_album_upload():
    assert is_acceptable_match(track(), yt_result(title="Man in the Box (Album)")) is False


def test_rejects_large_duration_mismatch():
    assert is_acceptable_match(track(), yt_result(duration_seconds=400)) is False


def test_accepts_small_duration_difference():
    assert is_acceptable_match(track(), yt_result(duration_seconds=270)) is True


def test_missing_result_fields_are_tolerated():
    assert is_acceptable_match(track(), {"category": "Songs", "resultType": "song"}) is True


def test_to_query_format():
    assert to_query({"name": "Man in the Box", "artist_name": "Alice In Chains"}) == "Man in the Box - Alice In Chains"


# --- match_reason (diagnostics) ---

def test_match_reason_good_is_none():
    assert match_reason(track(), yt_result()) is None


def test_match_reason_reports_duration():
    reason = match_reason(track(), yt_result(duration_seconds=400))
    assert reason is not None and "duration" in reason


def test_match_reason_reports_live():
    reason = match_reason(track(), yt_result(title="Man in the Box (Live)"))
    assert reason is not None and "live" in reason


def test_match_reason_reports_category():
    reason = match_reason(track(), yt_result(category="Videos"))
    assert reason is not None and "category" in reason


# --- choose_song_match (selection + duration fallback) ---

def test_choose_picks_first_acceptable():
    results = [
        yt_result(videoId="v1", duration_seconds=268),  # within margin
        yt_result(videoId="v2", duration_seconds=270),
    ]
    result, is_fallback, _ = choose_song_match(track(), results)
    assert result["videoId"] == "v1"
    assert is_fallback is False


def test_choose_falls_back_to_closest_duration():
    # Spotify 268s; results at +32s and +82s, both beyond the 15s margin.
    results = [
        yt_result(videoId="far", duration_seconds=350),
        yt_result(videoId="closer", duration_seconds=300),
    ]
    result, is_fallback, _ = choose_song_match(track(), results)
    assert result["videoId"] == "closer"
    assert is_fallback is True


def test_choose_returns_none_when_only_non_duration_rejections():
    results = [
        yt_result(videoId="v1", title="Man in the Box (Live)"),
        yt_result(videoId="v2", resultType="playlist"),
    ]
    result, is_fallback, rejected = choose_song_match(track(), results)
    assert result is None
    assert is_fallback is False
    assert len(rejected) == 2


def test_choose_does_not_fallback_to_live_version():
    results = [yt_result(videoId="v1", title="Man in the Box (Live)")]
    result, _, _ = choose_song_match(track(), results)
    assert result is None


def test_choose_empty_results():
    result, is_fallback, rejected = choose_song_match(track(), [])
    assert result is None
    assert is_fallback is False
    assert rejected == []
