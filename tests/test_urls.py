from utils.urls import extract_playlist_id


def test_full_url_with_query_params():
    url = "https://open.spotify.com/playlist/0bFXt3PTlM32bRKGO6zh7p?si=abc123"
    assert extract_playlist_id(url) == "0bFXt3PTlM32bRKGO6zh7p"


def test_full_url_without_query_params():
    url = "https://open.spotify.com/playlist/0bFXt3PTlM32bRKGO6zh7p"
    assert extract_playlist_id(url) == "0bFXt3PTlM32bRKGO6zh7p"


def test_plain_id_passes_through():
    assert extract_playlist_id("0bFXt3PTlM32bRKGO6zh7p") == "0bFXt3PTlM32bRKGO6zh7p"
