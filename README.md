# EXPORTIFY

Exportify is a python script for downloading and tagging spotify playlists.

## INSTALLATION

1. Clone the repository:
```bash
git clone https://github.com/ceviert/exportify
```

2. Install required libraries:
```bash
pip install -r requirements.txt
```

3. Download and install WebDriver:
    - Follow the steps in [developer.chrome](https://developer.chrome.com/docs/chromedriver/downloads) for selecting the right version for your browser.

4. Add the WebDriver to `PATH`:
    - Follow [this](https://gist.github.com/ScribbleGhost/752ec213b57eef5f232053e04f9d0d54) guide.

5. Go to [Spotify for Developers](https://developer.spotify.com/documentation/web-api) and create a Web API app.

6. Set your environment variables:
    - Open `.env.example`:
    ```env
    SPOTIPY_CLIENT_ID=your_client_id
    SPOTIPY_CLIENT_SECRET=your_client_secret
    BROWSER_NAME=your_browser_name
    ```
    - Change them according to your client id, client secret and browser name (`chrome` for Chrome, `brave` for Brave etc.)
    - Rename the file `.env.example` to `.env`.

## USAGE

Run the script from terminal with:
```bash
py main.py
```

## KNOWN-ISSUES

- If the playlist contains podcast, the script wont work.