"""Read Spotify playlists, preferring anonymous access with a credential fallback.

By default ("auto" mode) the client uses the same anonymous access token Spotify's
web player obtains before a user logs in, so no developer credentials are needed.
If the network blocks that anonymous token endpoint (some ISPs/regions do), and
SPOTIFY_CLIENT_ID/SECRET are set, it transparently falls back to the classic
spotipy client-credentials flow. Set SPOTIFY_AUTH=anonymous|credentials to force
either path.

Both paths only read *public* playlists.
"""

import os
import time

import requests

from config import settings
from spotify.tracks import track_to_dict
from utils.json_controller import load_from_file, save_to_file
from utils.logger import log, BRIGHT_YELLOW, RESET

# The web player's own client id, used only as a fallback on the token request
# (it ships in Spotify's public web player bundle; not a secret).
WEB_PLAYER_CLIENT_ID = "65b708073fc0480ea92a077233ca87bd"
TOKEN_URL = "https://open.spotify.com/get_access_token"
API_BASE = "https://api.spotify.com/v1"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)
# Headers mimicking the real web player so Spotify's edge serves JSON rather
# than a bot-detection block page to our token requests.
BROWSER_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Upgrade-Insecure-Requests": "1",
}
# Never use a token within this many seconds of its expiry.
TOKEN_TTL_BUFFER_SECONDS = 60
# How many tracks a playlist page request asks for (max allowed by the API).
PLAYLIST_PAGE_LIMIT = 100


# --- anonymous token machinery ---

def _new_session() -> requests.Session:
    """A session that looks like the web player to Spotify's edge."""
    session = requests.Session()
    session.headers.update(BROWSER_HEADERS)
    return session


def _fetch_anonymous_token():
    """Fetch an anonymous web-player token, mimicking the web player bootstrap.

    Returns (token, expires_at_ms). The real player first loads open.spotify.com
    to pick up anonymous cookies (sp_t, etc.) and then calls get_access_token; a
    bare request is often answered with an HTML block page instead of JSON. We
    replicate that bootstrap, trying both the bare and client-id query variants.
    Raises RuntimeError with a diagnostic message if all attempts fail.
    """
    params_variants = [
        {"reason": "transport", "productType": "web_player"},
        {"reason": "transport", "productType": "web_player", "clientId": WEB_PLAYER_CLIENT_ID},
    ]

    last_error = None
    for params in params_variants:
        session = _new_session()
        try:
            # Warm up the session so Spotify's edge hands us an anonymous
            # session cookie before we ask for a token.
            session.get("https://open.spotify.com/", timeout=15)
        except requests.RequestException as e:
            last_error = f"couldn't load open.spotify.com: {e}"
            continue

        try:
            resp = session.get(TOKEN_URL, params=params, timeout=15)
            data = resp.json()
        except requests.RequestException as e:
            last_error = f"token request failed: {e}"
            continue
        except ValueError as e:
            last_error = (
                f"token endpoint returned non-JSON (HTTP {resp.status_code}); "
                f"likely a block/consent page: {resp.text[:120]!r}"
            )
            continue

        token = data.get("accessToken")
        expires_at = data.get("accessTokenExpirationTimestampMs")
        if token and expires_at:
            return token, int(expires_at)
        last_error = f"unexpected token response (HTTP {resp.status_code}): {data}"

    raise RuntimeError(
        f"Failed to obtain an anonymous Spotify token: {last_error}. "
        "This is usually an anti-bot block: try disabling a VPN/proxy (e.g. "
        "Cloudflare WARP) or switching networks, then rerun."
    )


def _load_or_refresh_token() -> str:
    """Return a valid anonymous token, reusing the on-disk cache while it's fresh.

    The token lives in data/.spotify_token.json so separate `docker compose run`
    invocations can share it instead of refetching on every run.
    """
    cache_path = settings.spotify_token_cache_path
    cached = load_from_file(cache_path)
    if cached:
        token = cached.get("accessToken")
        expires_at = cached.get("expiresAt")
        now_ms = time.time() * 1000
        if token and expires_at and now_ms < int(expires_at) - TOKEN_TTL_BUFFER_SECONDS * 1000:
            return token

    token, expires_at = _fetch_anonymous_token()
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    save_to_file({"accessToken": token, "expiresAt": expires_at}, cache_path)
    return token


# --- implementations ---

class _AnonymousClient:
    """Playlist reader using the anonymous web-player token (no credentials)."""

    def __init__(self):
        self._headers = {
            "Authorization": f"Bearer {_load_or_refresh_token()}",
            "User-Agent": USER_AGENT,
        }

    def _get_json(self, path: str, params: dict = None) -> dict:
        """GET an API endpoint, retrying transient failures with backoff.

        Raises immediately on auth errors (401/403), not-found (404), and other
        4xx responses; retries rate limits (honoring Retry-After) and 5xx errors.
        """
        url = API_BASE + path
        for attempt in range(3):
            try:
                resp = requests.get(url, params=params, headers=self._headers, timeout=30)
            except requests.RequestException as e:
                if attempt == 2:
                    raise RuntimeError(f"Network error contacting Spotify ({url}): {e}") from e
                time.sleep(2 ** attempt)
                continue

            if resp.status_code == 200:
                return resp.json()
            if resp.status_code == 429:
                retry_after = resp.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 2 ** attempt
                if attempt == 2:
                    raise RuntimeError(f"Rate limited by Spotify after retries ({url}).")
                log(f"Spotify rate limited; retrying in {delay:.0f}s...")
                time.sleep(delay)
                continue
            if resp.status_code in (401, 403):
                raise RuntimeError(
                    f"Spotify rejected the anonymous token (HTTP {resp.status_code}) for {url}. "
                    "The anonymous token may no longer be accepted by this endpoint."
                )
            if resp.status_code == 404:
                raise RuntimeError(f"Playlist not found (or private): {url}")
            if resp.status_code < 500:
                raise RuntimeError(
                    f"Spotify API error HTTP {resp.status_code} for {url}: {resp.text[:200]}"
                )
            if attempt == 2:
                raise RuntimeError(
                    f"Spotify API error HTTP {resp.status_code} after retries for {url}: {resp.text[:200]}"
                )
            time.sleep(2 ** attempt)

        raise RuntimeError(f"Exhausted retries for {url}")  # pragma: no cover

    def get_pl_info(self, pl_id: str) -> dict:
        data = self._get_json(f"/playlists/{pl_id}", params={"fields": "name,tracks.total"})
        return {
            "playlist_name": data["name"],
            "track_count": data["tracks"]["total"],
        }

    def get_pl_items(self, pl_id: str) -> list:
        fields = (
            "next,items.track.id,items.track.name,items.track.artists.name,"
            "items.track.album.name,items.track.album.images,items.track.duration_ms"
        )
        results = []
        offset = 0

        while True:
            data = self._get_json(
                f"/playlists/{pl_id}/tracks",
                params={"offset": offset, "limit": PLAYLIST_PAGE_LIMIT, "fields": fields},
            )
            items = data.get("items", [])
            results.extend(items)
            if not data.get("next"):
                break
            offset += len(items)

        return [entry for entry in (track_to_dict(item) for item in results) if entry]

    def get_pl_data(self, pl_id: str) -> dict:
        return {
            **self.get_pl_info(pl_id),
            "tracks": self.get_pl_items(pl_id),
        }


class _CredentialsClient:
    """Playlist reader using Spotify developer credentials via spotipy."""

    def __init__(self):
        # Lazy import: only needed if falling back to credentials mode.
        import spotipy
        from spotipy.oauth2 import SpotifyClientCredentials
        from spotipy.cache_handler import CacheFileHandler

        client_id = settings.spotify_client_id
        client_secret = settings.spotify_client_secret
        if not client_id or not client_secret:
            raise ValueError(
                "Missing Spotify API credentials (SPOTIFY_CLIENT_ID/SECRET) in .env"
            )

        self.sp = spotipy.Spotify(
            auth_manager=SpotifyClientCredentials(
                client_id=client_id,
                client_secret=client_secret,
                cache_handler=CacheFileHandler(cache_path=settings.spotipy_cache_path),
            ),
            retries=5,        # retry on connection errors
            status_retries=3  # retry on 429/5xx responses (uses backoff)
        )

    def get_pl_info(self, pl_id: str) -> dict:
        response = self.sp.playlist(playlist_id=pl_id, fields="name, tracks.total")
        return {
            "playlist_name": response["name"],
            "track_count": response["tracks"]["total"],
        }

    def get_pl_items(self, pl_id: str) -> list:
        results = []
        offset = 0

        while True:
            response = self.sp.playlist_items(
                playlist_id=pl_id,
                offset=offset,
                fields="next,items.track.id,items.track.name,items.track.artists.name,"
                       "items.track.album.name,items.track.album.images,items.track.duration_ms",
            )
            items = response.get("items", [])
            results.extend(items)
            if not response.get("next"):
                break
            offset += len(items)

        return [entry for entry in (track_to_dict(item) for item in results) if entry]

    def get_pl_data(self, pl_id: str) -> dict:
        return {
            **self.get_pl_info(pl_id),
            "tracks": self.get_pl_items(pl_id),
        }


def _pick_impl():
    """Choose a playlist reader based on SPOTIFY_AUTH and what the network allows."""
    mode = settings.spotify_auth_mode

    if mode == "credentials":
        return _CredentialsClient()
    if mode == "anonymous":
        return _AnonymousClient()

    # auto (default): anonymous first, fall back to credentials when the token
    # path is blocked (e.g. certain ISPs/regions).
    try:
        return _AnonymousClient()
    except RuntimeError as e:
        if settings.spotify_client_id and settings.spotify_client_secret:
            log(f"{BRIGHT_YELLOW}Anonymous Spotify access blocked ({e}); "
                f"falling back to developer credentials.{RESET}")
            return _CredentialsClient()
        raise


class SpotifyClient:
    """Facade over the anonymous or credential-backed playlist readers.

    Auto mode (the default) tries the anonymous web-player token first and
    transparently falls back to developer credentials when the network blocks the
    token endpoint. Set SPOTIFY_AUTH=anonymous|credentials to force one path.
    """

    def __init__(self):
        self._impl = _pick_impl()

    def get_pl_info(self, pl_id: str) -> dict:
        return self._impl.get_pl_info(pl_id)

    def get_pl_items(self, pl_id: str) -> list:
        return self._impl.get_pl_items(pl_id)

    def get_pl_data(self, pl_id: str) -> dict:
        return self._impl.get_pl_data(pl_id)
