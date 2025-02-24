from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from webdriver_manager.chrome import ChromeDriverManager
from pytube import YouTube
from pytube import Search
import os
from pydub import AudioSegment
import yt_dlp
import re
from datetime import datetime
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import requests
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, APIC, error
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import ytmusicapi
import sys
import io
from dotenv import load_dotenv
import json
from unidecode import unidecode

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))

ydl_opts = {
    'format': 'bestaudio/best',
    'outtmpl': '%(title)s.%(ext)s',
    # 'cookies': 'cookies.txt',
    # 'cookiesfrombrowser': (os.getenv("BROWSER_NAME"),)
}

def get_first_part_before_comma(input_string):
    return input_string.split(',', 1)[0]

def get_album_id_from_track_id(track_id):
    try:
        # Fetch track details
        track_info = sp.track(track_id)
        # Retrieve and return the album ID
        album_id = track_info['album']['id']
        return album_id
    except spotipy.exceptions.SpotifyException as e:
        print(f"Error fetching album ID: {e}", flush=True)
        return None

def get_album_image(album_id):
    album = sp.album(album_id)
    if album and album['images']:
        image_url = album['images'][0]['url']
        print(f"Image URL: {image_url}", flush=True)
        return image_url
    else:
        print("No images found for this album.", flush=True)
        return None
    
def download_image(url, path, retries=3):

    os.makedirs(os.path.dirname(path), exist_ok=True)

    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()  
            with open(path, 'wb') as file:
                file.write(response.content)
            print(f"Downloaded image to {path}", flush=True)
            break  
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1} failed: {e}", flush=True)
            time.sleep(2)
    else:
        print("Failed to download image after multiple attempts.", flush=True)

def tag_mp3(mp3_path, artist, title, album, cover_art_path):
    audio = MP3(mp3_path, ID3=ID3)
    
    try:
        audio.add_tags()
    except error:
        pass
    
    audio.tags["TIT2"] = TIT2(encoding=3, text=title)
    
    audio.tags["TPE1"] = TPE1(encoding=3, text=artist)
    
    audio.tags["TALB"] = TALB(encoding=3, text=album)
    
    with open(cover_art_path, "rb") as img_file:
        audio.tags["APIC"] = APIC(
            encoding=3,
            mime="image/jpeg",
            type=3,
            desc="Cover",
            data=img_file.read()
        )
    
    audio.save()
    print(f"Tagged '{mp3_path}' with artist '{artist}', title '{title}', album '{album}', and cover art.", flush=True)

plurl = sys.argv[1]

start_time = time.time()

print("launching webdriver", flush=True)
driver = webdriver.Chrome()
driver.get('https://www.chosic.com/spotify-playlist-analyzer/')
driver.implicitly_wait(10)

inputfield = driver.find_element(By.ID, 'search-word')
inputfield.send_keys(plurl)
analyzebutton = driver.find_element(By.ID, 'analyze')
analyzebutton.click()
print("analyzing playlist...", flush=True)
time.sleep(2)
while True:
    loadingbar= driver.find_element(By.ID, 'myBar')
    print(loadingbar.text, flush=True)
    if len(loadingbar.text) == 0:
        break
print("analyzing done.", flush=True)

plname = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "pl-name")))
print("playlist name is" , plname.text, flush=True)

tempsongcount = driver.find_element(By.CLASS_NAME, 'total-tracks')
time.sleep(2)

templist = []
for element in tempsongcount.text:
    if element == ' ':
        break
    templist.append(element)
songcounttext = "".join(templist)
songcount = int(songcounttext)
print("playlist has " , songcount , " songs.", flush=True)

scrollto = driver.find_element(By.ID, 'all-tracks-table')
driver.execute_script("arguments[0].scrollIntoView(true);", scrollto)
time.sleep(3)

songnames = driver.find_elements(By.CLASS_NAME, 'td-name-text.check-table-song')
# print(len(songnames))
songcount = min(songcount, len(songnames))

tempforartist = driver.find_elements(By.CLASS_NAME, 'td-number.oferflow')

artists = []
i = 0
for element in tempforartist:
    if i % 4 == 0:
        artists.append(element)
    i += 1
# print(len(artists))

album_elements = driver.find_elements(By.XPATH, '//*[@id="tracks-table"]/tbody/tr/td[8]')

albumnames = []
i = 0
for element in album_elements:
    albumnames.append(element.text)

print("len(albumnames) = " + str(len(albumnames)), flush=True)

for album in albumnames:
    time.sleep(0.1)
    print("-> " + unidecode(album), flush=True)

albumcount = len(albumnames)

trackidelements = driver.find_elements(By.XPATH, '//*[@id="tracks-table"]/tbody/tr/td[22]')

trackids = []
i = 0
for element in trackidelements:
    trackids.append(element.text)

for trackid in trackids:
    time.sleep(0.1)
    print("-> " + trackid, flush=True)

namesandartists = []
i = 0
while i < songcount:
    full = artists[i].text + " - " + songnames[i].text
    namesandartists.append(full)
    i += 1
print("song names and artists scraped, starting download...", flush=True)
time.sleep(2)

savedir = f"Music/{re.sub(r'[<>:"/\\|?*.]', "", plname.text)}"
songlist = savedir + "/list.txt"

if not os.path.exists(savedir):
    os.makedirs(savedir)

with open(songlist, "a+", encoding="utf-8") as file:
    file.seek(0)
    lines = file.read().splitlines()
    if lines:
        lines.pop()
    print("Lines read from file:", lines, flush=True)

with open(songlist, "w", encoding="utf-8") as file:
    if plname.text not in lines:
        file.write(plname.text + "\n=================\n")
    for line in lines:
        file.write(line + "\n") 

downloaded = []

with open("data/songcache.json", "r") as file:
    loaded_data = json.load(file)

i = 0
saved = 0
for song, trackid in zip(namesandartists, trackids):
    
    if song in lines:
        print(song + " ALREADY DOWNLOADED", flush=True)
        i += 1
        saved += 1
        print("===============================================", flush=True)
        print("---OVERALL PROGRESS--- >>> " , i * 100 / songcount , "%", flush=True)
        print("===============================================", flush=True)
        continue

    if trackid in loaded_data:
      print(song + " ALREADY CACHED, DOWNLOADING...", flush=True)
      videoId = loaded_data[trackid]

    else:
        ytm = ytmusicapi.YTMusic()
        query = song
        search_results = ytm.search(query)
        # print(search_results)
        for result in search_results:
            if isinstance(result, dict) and 'resultType' in result:
                if result['resultType'] == 'song' and result['category'] in ['Songs', 'Top result']:  # Ensure it's a song
                    print(f"Video ID: {result['videoId']}", flush=True)
                    videoId = result['videoId']
                    break

    video_url = f"https://www.youtube.com/watch?v={videoId}"

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        print(song + f"\nDownloading video with ID: {videoId}", flush=True)
        ydl.download([video_url])
        info_dict = ydl.extract_info(video_url, download=False)
        video_file = ydl.prepare_filename(info_dict)

    songname = re.sub(r'[\\/*?:"<>|.İ]', "", namesandartists[i])
    mp3_file_name = re.sub(r'[<>:"/\\|?*İ]', "", (os.path.splitext(songname)[0] + '.mp3'))
    mp3_file_path = os.path.join(savedir, mp3_file_name)
    AudioSegment.from_file(video_file).export(mp3_file_path, format='mp3')
    os.remove(video_file)
    i += 1
    saved += 1

    downloaded.append(song)

    print("===============================================", flush=True)
    print("---OVERALL PROGRESS--- >>> " , i * 100 / songcount , "%", flush=True)
    print("===============================================", flush=True)

try:
    with open(songlist, "r", encoding="utf-8") as file:
        existing_songs = file.read().splitlines()
except FileNotFoundError:
    existing_songs = []

with open(songlist, "a", encoding="utf-8") as file:
    for song in downloaded:
        if song not in existing_songs:
            file.write(song + "\n")
    now = datetime.now()
    formatted_date = now.strftime("%Y-%m-%d %H:%M:%S")
    file.write("\nLast updated at " + formatted_date + "\n")

end_time = time.time()
time_elapsed = end_time - start_time
print("Time elapsed => " + str(time_elapsed) + " seconds.", flush=True)

print("\033[1;32;40mDOWNLOADS ARE DONE. STARTING THE TAGGING PROCESS...\033[0m")

i = 0
tagged = 0
for album in albumnames:

    print(album)

    album_id = get_album_id_from_track_id(trackids[i])
    albumimgurl = get_album_image(album_id)
    albumsavedir = f"Music/{re.sub(r'[<>:"/\\|?*.]', "", plname.text)}/album_covers"
    songname = re.sub(r'[\\/*?:"<>|.İ]', "", namesandartists[i])
    album_file_name = re.sub(r'[<>:"/\\|?*İ]', "", (os.path.splitext(songname)[0] + '.jpg'))
    album_file_path = os.path.join(albumsavedir, album_file_name)

    songname = re.sub(r'[\\/*?:"<>|.İ]', "", namesandartists[i])
    mp3_file_name = re.sub(r'[<>:"/\\|?*İ]', "", (os.path.splitext(songname)[0] + '.mp3'))
    mp3_file_path = os.path.join(savedir, mp3_file_name)
    
    download_image(albumimgurl, album_file_path)

    tag_mp3(mp3_file_path, artists[i].text, songnames[i].text, albumnames[i], album_file_path)

    i += 1
    tagged += 1

    print("===============================================", flush=True)
    print("---OVERALL PROGRESS--- >>> " , i * 100 / albumcount , "%", flush=True)
    print("===============================================", flush=True)

driver.quit()