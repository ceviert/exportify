# 🎧 Exportify

Exportify is a fully automated, Dockerized pipeline that clones your Spotify playlists directly into perfectly tagged local MP3 files using the YouTube Music backend.

## ✨ Features
* **Perfect Metadata:** Every downloaded `.mp3` is automatically injected with the official Spotify ID3 tags (Title, Artist, Album) and the high-resolution album cover art.
* **Duration-Aware Matching:** The native search algorithm compares YouTube Music results against Spotify's official millisecond track durations, actively skipping incorrect "Live" versions, extended mixes, or full-album videos.
* **Global Sync:** Exportify remembers your playlists natively. The `sync` command organically scans your downloads folder and artificially pulls in missing new songs while deleting tracks that you've removed from your Spotify playlist.
* **Smart Caching:** Local database queries prevent double-searching the same track twice.

## 📋 Prerequisites

Before running Exportify, ensure you have the following installed on your system:
* [Docker](https://docs.docker.com/get-docker/)
* [Docker Compose](https://docs.docker.com/compose/install/)

## 🚀 Setup

1. Rename the `.env` template or create a new `.env` file in the root of the project.
2. **No Spotify developer credentials needed by default.** Playlists are read
   through Spotify's anonymous web-player token:
```env
CACHE_PATH="data/songcache.json"
```
3. On networks that block that anonymous endpoint (some ISPs/regions), Exportify
   automatically falls back to developer credentials if you set them:
```env
SPOTIFY_CLIENT_ID="your_spotify_client_id_here"
SPOTIFY_CLIENT_SECRET="your_spotify_client_secret_here"
```
   `SPOTIFY_AUTH` controls the mode: `auto` (default — anonymous, then
   credentials), `anonymous`, or `credentials`.

> Note: both access paths only read **public** playlists. Private playlists are
> not supported.

## 💻 Usage

Exportify is completely containerized. All commands should be run using `docker compose` to ensure you are utilizing the isolated `yt-dlp` and `ffmpeg` backend.

### 1. Download a Playlist
You can download one or multiple playlists synchronously. The script natively caches the IDs, downloads the audio, extracts the MP3, and tags it:
```bash
sudo docker compose run app python app/main.py --action download --playlist "YOUR_SPOTIFY_URL_1" "YOUR_SPOTIFY_URL_2"
```

### 2. Cache Only
If you only want to build your local `songcache.json` matching database without actually downloading the gigabytes of audio yet:
```bash
sudo docker compose run app python app/main.py --action cache --playlist "YOUR_SPOTIFY_URL"
```

### 3. Global Sync
Keep your local pristine MP3 library perfectly mirroring your live Spotify library. The Global Sync command scans your previously downloaded folders, pulls down any new songs added to Spotify, and deletes any `.mp3` files you removed from the app:
```bash
sudo docker compose run app python app/main.py --action sync
```

### 4. Age-Restricted Tracks (Optional)
On very rare occasions, YouTube tags official intense music videos as mathematically 18+ (Explicit). If the pipeline runs into one, `yt-dlp` will safely reject it and log an age-restriction error. 
To unlock these organically:
1. Use a browser extension like **"Get cookies.txt LOCALLY"**.
2. Go to YouTube (logged into an adult account).
3. Export your cookies and save them natively to `data/cookies.txt` exactly.
4. Exportify actively scans for this file. If it finds it, it statically impersonates your browser and bypasses all age locks organically!