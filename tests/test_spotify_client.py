import sys
import time
from unittest import mock

import pytest

from config import settings
from spotify.client import (
    SpotifyClient,
    _AnonymousClient,
    _CredentialsClient,
    _fetch_anonymous_token,
    _load_or_refresh_token,
    _pick_impl,
)
from utils.json_controller import load_from_file, save_to_file

NOW_MS = int(time.time() * 1000)
FUTURE_MS = NOW_MS + 3_600_000


def _install_fake_spotipy(monkeypatch):
    """Register a fake spotipy package so _CredentialsClient.__init__ imports."""
    spotipy = mock.Mock()
    spotipy.Spotify = mock.Mock()
    spotipy.oauth2 = mock.Mock(SpotifyClientCredentials=mock.Mock())
    spotipy.cache_handler = mock.Mock(CacheFileHandler=mock.Mock())
    monkeypatch.setitem(sys.modules, "spotipy", spotipy)
    monkeypatch.setitem(sys.modules, "spotipy.oauth2", spotipy.oauth2)
    monkeypatch.setitem(sys.modules, "spotipy.cache_handler", spotipy.cache_handler)


# --- _fetch_anonymous_token ---

def test_fetch_anonymous_token_parses_response():
    payload = {
        "accessToken": "abc123",
        "accessTokenExpirationTimestampMs": FUTURE_MS,
        "isAnonymous": True,
    }
    token_resp = mock.Mock(status_code=200)
    token_resp.json.return_value = payload

    session = mock.Mock()
    session.get.return_value = token_resp  # homepage warmup + token request

    with mock.patch("spotify.client._new_session", return_value=session) as new_session:
        token, expires_at = _fetch_anonymous_token()

    assert token == "abc123"
    assert expires_at == FUTURE_MS
    # Session was warmed up (homepage) before the token request.
    assert session.get.call_count == 2
    # First (bare) variant succeeded; no client-id fallback needed.
    new_session.assert_called_once()


def test_fetch_anonymous_token_falls_back_to_client_id_variant():
    payload = {"accessToken": "via-client-id", "accessTokenExpirationTimestampMs": FUTURE_MS}

    error_resp = mock.Mock(status_code=200)
    error_resp.json.return_value = {"error": "invalid request"}
    session1 = mock.Mock()
    session1.get.return_value = error_resp

    token_resp = mock.Mock(status_code=200)
    token_resp.json.return_value = payload
    session2 = mock.Mock()
    session2.get.return_value = token_resp

    with mock.patch("spotify.client._new_session", side_effect=[session1, session2]):
        token, _ = _fetch_anonymous_token()

    assert token == "via-client-id"
    # The fallback session's token request carried the web-player client id.
    _, kwargs = session2.get.call_args_list[1]
    assert kwargs["params"]["clientId"]


def test_fetch_anonymous_token_raises_on_blocked_response():
    blocked = mock.Mock(status_code=403)
    blocked.json.side_effect = ValueError("Expecting value: line 2 column 1 (char 1)")
    blocked.text = "<html>URL Blocked</html>"

    session = mock.Mock()
    session.get.return_value = blocked

    with mock.patch("spotify.client._new_session", return_value=session):
        with pytest.raises(RuntimeError, match="anonymous Spotify token"):
            _fetch_anonymous_token()
    assert session.get.call_count == 4  # 2 variants x (homepage + token)


def test_fetch_anonymous_token_raises_on_error_body():
    resp = mock.Mock(status_code=200)
    resp.json.return_value = {"error": "unauthorized"}

    session = mock.Mock()
    session.get.return_value = resp

    with mock.patch("spotify.client._new_session", return_value=session):
        with pytest.raises(RuntimeError, match="anonymous Spotify token"):
            _fetch_anonymous_token()


# --- _load_or_refresh_token (on-disk cache) ---

def test_token_cache_reused_when_fresh(tmp_path, monkeypatch):
    cache_file = tmp_path / "token.json"
    monkeypatch.setattr(settings, "spotify_token_cache_path", str(cache_file))
    save_to_file({"accessToken": "cached-token", "expiresAt": FUTURE_MS}, str(cache_file))

    with mock.patch("spotify.client._fetch_anonymous_token") as fetch:
        token = _load_or_refresh_token()

    assert token == "cached-token"
    fetch.assert_not_called()


def test_token_cache_refreshed_when_expired(tmp_path, monkeypatch):
    cache_file = tmp_path / "token.json"
    monkeypatch.setattr(settings, "spotify_token_cache_path", str(cache_file))
    save_to_file({"accessToken": "stale", "expiresAt": NOW_MS - 1_000}, str(cache_file))

    with mock.patch(
        "spotify.client._fetch_anonymous_token", return_value=("fresh-token", FUTURE_MS)
    ):
        token = _load_or_refresh_token()

    assert token == "fresh-token"
    cached = load_from_file(str(cache_file))
    assert cached["accessToken"] == "fresh-token"


def test_token_cache_ignores_corrupt_file_and_fetches(tmp_path, monkeypatch):
    cache_file = tmp_path / "token.json"
    monkeypatch.setattr(settings, "spotify_token_cache_path", str(cache_file))
    cache_file.write_text("{not valid json")

    with mock.patch(
        "spotify.client._fetch_anonymous_token", return_value=("fresh-token", FUTURE_MS)
    ):
        token = _load_or_refresh_token()

    assert token == "fresh-token"


# --- _get_json ---

def _anon_client():
    client = _AnonymousClient.__new__(_AnonymousClient)
    client._headers = {"Authorization": "Bearer t", "User-Agent": "test"}
    return client


def test_get_json_raises_immediately_on_token_rejection():
    client = _anon_client()
    resp = mock.Mock(status_code=401)
    with mock.patch("spotify.client.requests.get", return_value=resp) as mocked:
        with pytest.raises(RuntimeError, match="rejected the anonymous token"):
            client._get_json("/playlists/x")
    mocked.assert_called_once()  # auth errors are not retried


def test_get_json_raises_on_not_found():
    client = _anon_client()
    resp = mock.Mock(status_code=404)
    with mock.patch("spotify.client.requests.get", return_value=resp):
        with pytest.raises(RuntimeError, match="not found"):
            client._get_json("/playlists/x")


def test_get_json_retries_on_rate_limit_then_succeeds():
    client = _anon_client()
    rate_limited = mock.Mock(status_code=429, headers={"Retry-After": "0"})
    ok = mock.Mock(status_code=200)
    ok.json.return_value = {"hello": "world"}
    with mock.patch(
        "spotify.client.requests.get", side_effect=[rate_limited, ok]
    ) as mocked:
        data = client._get_json("/playlists/x")

    assert data == {"hello": "world"}
    assert mocked.call_count == 2


def test_get_json_retries_on_5xx_then_succeeds():
    client = _anon_client()
    server_error = mock.Mock(status_code=502)
    ok = mock.Mock(status_code=200)
    ok.json.return_value = {"ok": True}
    with mock.patch(
        "spotify.client.requests.get", side_effect=[server_error, ok]
    ):
        assert client._get_json("/playlists/x") == {"ok": True}


# --- public methods ---

def test_get_pl_info():
    client = _anon_client()
    with mock.patch.object(
        client, "_get_json", return_value={"name": "Be Quiet & Drive", "tracks": {"total": 96}}
    ) as get:
        info = client.get_pl_info("pl1")

    assert info == {"playlist_name": "Be Quiet & Drive", "track_count": 96}
    get.assert_called_once_with("/playlists/pl1", params={"fields": "name,tracks.total"})


def test_get_pl_items_paginates_and_maps():
    client = _anon_client()
    page1 = {
        "next": "https://api.spotify.com/v1/playlists/pl1/tracks?offset=1",
        "items": [{
            "track": {
                "id": "t1", "name": "Rooster",
                "artists": [{"name": "Alice In Chains"}],
                "album": {"name": "Dirt", "images": [{"url": "http://img/1.jpg"}]},
                "duration_ms": 370000,
            }
        }],
    }
    page2 = {
        "next": None,
        "items": [{
            "track": {
                "id": "t2", "name": "Nutshell",
                "artists": [{"name": "Alice In Chains"}],
                "album": {"name": "Jar of Flies", "images": [{"url": "http://img/2.jpg"}]},
                "duration_ms": 260000,
            }
        }],
    }
    with mock.patch.object(client, "_get_json", side_effect=[page1, page2]) as get:
        tracks = client.get_pl_items("pl1")

    assert get.call_count == 2
    assert [t["id"] for t in tracks] == ["t1", "t2"]
    assert tracks[0]["artist_name"] == "Alice In Chains"
    assert tracks[1]["cover_url"] == "http://img/2.jpg"


def test_get_pl_data_merges_info_and_items():
    client = _anon_client()
    with mock.patch.object(client, "get_pl_info", return_value={"playlist_name": "P", "track_count": 1}):
        with mock.patch.object(client, "get_pl_items", return_value=[{"id": "t1"}]):
            data = client.get_pl_data("pl1")

    assert data["playlist_name"] == "P"
    assert data["track_count"] == 1
    assert data["tracks"] == [{"id": "t1"}]


# --- _pick_impl / SpotifyClient facade (auto fallback) ---

def test_pick_impl_auto_prefers_anonymous(monkeypatch):
    monkeypatch.setattr(settings, "spotify_auth_mode", "auto")
    anon = object()
    with mock.patch("spotify.client._AnonymousClient", return_value=anon) as a:
        assert _pick_impl() is anon
    a.assert_called_once_with()


def test_pick_impl_auto_falls_back_to_credentials_when_blocked(monkeypatch):
    monkeypatch.setattr(settings, "spotify_auth_mode", "auto")
    monkeypatch.setattr(settings, "spotify_client_id", "cid")
    monkeypatch.setattr(settings, "spotify_client_secret", "csecret")
    creds = object()
    with mock.patch("spotify.client._AnonymousClient", side_effect=RuntimeError("blocked")):
        with mock.patch("spotify.client._CredentialsClient", return_value=creds) as c:
            assert _pick_impl() is creds
    c.assert_called_once_with()


def test_pick_impl_auto_raises_when_blocked_and_no_creds(monkeypatch):
    monkeypatch.setattr(settings, "spotify_auth_mode", "auto")
    monkeypatch.setattr(settings, "spotify_client_id", "")
    monkeypatch.setattr(settings, "spotify_client_secret", "")
    with mock.patch("spotify.client._AnonymousClient", side_effect=RuntimeError("blocked")):
        with pytest.raises(RuntimeError, match="blocked"):
            _pick_impl()


def test_pick_impl_credentials_forced(monkeypatch):
    monkeypatch.setattr(settings, "spotify_auth_mode", "credentials")
    creds = object()
    with mock.patch("spotify.client._CredentialsClient", return_value=creds) as c:
        assert _pick_impl() is creds
    c.assert_called_once_with()


def test_pick_impl_anonymous_forced(monkeypatch):
    monkeypatch.setattr(settings, "spotify_auth_mode", "anonymous")
    anon = object()
    with mock.patch("spotify.client._AnonymousClient", return_value=anon) as a:
        assert _pick_impl() is anon
    a.assert_called_once_with()


def test_facade_delegates_to_picked_impl():
    impl = mock.Mock()
    impl.get_pl_info.return_value = {"playlist_name": "P", "track_count": 1}
    impl.get_pl_items.return_value = [{"id": "t1"}]
    impl.get_pl_data.return_value = {"playlist_name": "P", "track_count": 1, "tracks": [{"id": "t1"}]}
    with mock.patch("spotify.client._pick_impl", return_value=impl):
        client = SpotifyClient()

    assert client.get_pl_info("pl1") == {"playlist_name": "P", "track_count": 1}
    assert client.get_pl_items("pl1") == [{"id": "t1"}]
    assert client.get_pl_data("pl1") == {"playlist_name": "P", "track_count": 1, "tracks": [{"id": "t1"}]}
    impl.get_pl_info.assert_called_once_with("pl1")
    impl.get_pl_items.assert_called_once_with("pl1")
    impl.get_pl_data.assert_called_once_with("pl1")


# --- _CredentialsClient ---

def test_credentials_client_requires_creds(monkeypatch):
    monkeypatch.setattr(settings, "spotify_client_id", "")
    monkeypatch.setattr(settings, "spotify_client_secret", "")
    # spotipy may not be installed in this env; the import happens lazily
    # inside __init__, so stub it out to reach the credentials check.
    _install_fake_spotipy(monkeypatch)
    with pytest.raises(ValueError, match="Missing Spotify API credentials"):
        _CredentialsClient()


def test_credentials_get_pl_info():
    client = _CredentialsClient.__new__(_CredentialsClient)
    client.sp = mock.Mock()
    client.sp.playlist.return_value = {"name": "P", "tracks": {"total": 5}}
    assert client.get_pl_info("pl1") == {"playlist_name": "P", "track_count": 5}
    client.sp.playlist.assert_called_once_with(playlist_id="pl1", fields="name, tracks.total")


def test_credentials_get_pl_items_paginates():
    client = _CredentialsClient.__new__(_CredentialsClient)
    client.sp = mock.Mock()
    client.sp.playlist_items.side_effect = [
        {"next": "page2", "items": [{
            "track": {"id": "t1", "name": "Rooster",
                      "artists": [{"name": "Alice In Chains"}],
                      "album": {"name": "Dirt", "images": [{"url": "http://img/1.jpg"}]},
                      "duration_ms": 370000}}]},
        {"next": None, "items": [{
            "track": {"id": "t2", "name": "Nutshell",
                      "artists": [{"name": "Alice In Chains"}],
                      "album": {"name": "Jar of Flies", "images": [{"url": "http://img/2.jpg"}]},
                      "duration_ms": 260000}}]},
    ]
    tracks = client.get_pl_items("pl1")
    assert client.sp.playlist_items.call_count == 2
    assert [t["id"] for t in tracks] == ["t1", "t2"]
