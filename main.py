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

def split_artist_and_song(input_string):
    parts = input_string.split(" - ")
    if len(parts) == 2:
        artist, song = parts[0].strip(), parts[1].strip()
        return artist, song
    else:
        print("String format is not 'Artist - Song Title'.")
        return None, None

def get_first_part_before_dash(input_string):
    return input_string.split('-', 1)[0]

def get_album_id_from_track_id(track_id):
    try:
        # Fetch track details
        track_info = sp.track(track_id)
        # Retrieve and return the album ID
        album_id = track_info['album']['id']
        return album_id
    except spotipy.exceptions.SpotifyException as e:
        print(f"Error fetching album ID: {e}")
        return None

def get_album_image(album_id):
    album = sp.album(album_id)
    if album and album['images']:
        image_url = album['images'][0]['url']
        print(f"Image URL: {image_url}")
        return image_url
    else:
        print("No images found for this album.")
        return None
    
def download_image(url, path, retries=3):

    os.makedirs(os.path.dirname(path), exist_ok=True)

    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()  
            with open(path, 'wb') as file:
                file.write(response.content)
            print(f"Downloaded image to {path}")
            break  
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(2)  # Wait before retrying
    else:
        print("Failed to download image after multiple attempts.")

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
    print(f"Tagged '{mp3_path}' with artist '{artist}', title '{title}', album '{album}', and cover art.")

def song_to_youtube_url(song):
    ytm = ytmusicapi.YTMusic()
    query = song
    search_results = ytm.search(query)
    # print(search_results)
    for result in search_results:
        if isinstance(result, dict) and 'resultType' in result:
            if result['resultType'] == 'song' and result['category'] in ['Songs', 'Top result']:  # Ensure it's a song
                print(f"Video ID: {result['videoId']}")
                videoId = result['videoId']
                break

    return f"https://www.youtube.com/watch?v={videoId}"

plurl = input("provide the playlist url >> ")

start_time = time.time()

print("launching webdriver")
driver = webdriver.Chrome()
driver.get('https://www.chosic.com/spotify-playlist-analyzer/')
driver.implicitly_wait(10)

inputfield = driver.find_element(By.ID, 'search-word')
inputfield.send_keys(plurl)
analyzebutton = driver.find_element(By.ID, 'analyze')
analyzebutton.click()
print("analyzing playlist...")
time.sleep(2)
while True:
    loadingbar= driver.find_element(By.ID, 'myBar')
    print(loadingbar.text)
    if len(loadingbar.text) == 0:
        break
print("analyzing done.")

plname = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "pl-name")))  # Replace with correct selector
print("playlist name is" , plname.text)

tempsongcount = driver.find_element(By.CLASS_NAME, 'total-tracks')
time.sleep(2)

templist = []
for element in tempsongcount.text:
    if element == ' ':
        break
    templist.append(element)
songcounttext = "".join(templist)
songcount = int(songcounttext)
print("playlist has " , songcount , " songs.")

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

print("len(albumnames) = " + str(len(albumnames)))

for album in albumnames:
    time.sleep(0.5)
    print("-> " + album.encode('ascii', 'ignore').decode('ascii'))

albumcount = len(albumnames)

year_elements = driver.find_elements(By.XPATH, '//*[@id="tracks-table"]/tbody/tr/td[9]')

yearlist = []
i = 0
for element in year_elements:
    yearlist.append(get_first_part_before_dash(element.text))

for year in yearlist:
    time.sleep(0.5)
    print("-> " + year)

trackidelements = driver.find_elements(By.XPATH, '//*[@id="tracks-table"]/tbody/tr/td[22]')

trackids = []
i = 0
for element in trackidelements:
    trackids.append(element.text)

for trackid in trackids:
    time.sleep(0.5)
    print("-> " + trackid)

namesandartists = []
i = 0
while i < songcount:
    full = artists[i].text + " - " + songnames[i].text
    namesandartists.append(full)
    i += 1
print("song names and artists scraped, starting download...")
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
    print("Lines read from file:", lines)

with open(songlist, "w", encoding="utf-8") as file:
    if plname.text not in lines:
        file.write(plname.text + "\n=================\n")
    for line in lines:
        file.write(line + "\n") 

downloaded = []

i = 0
saved = 0
for song in namesandartists:
    
    if song in lines:
        print(song + " ALREADY DONWLOADED")
        i += 1
        saved += 1
        print("===============================================")
        print("---OVERALL PROGRESS--- >>> " , i * 100 / songcount , "%")
        print("===============================================")
        continue

    video_url = song_to_youtube_url(song)

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        print(song + f"\nDownloading video with ID: {videoId}")
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

    print("===============================================")
    print("---OVERALL PROGRESS--- >>> " , i * 100 / songcount , "%")
    print("===============================================")

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
print("Time elapsed => " + str(time_elapsed) + " seconds.")

print("DOWNLOADS ARE DONE. STARTING THE TAGGING PROCESS...")

albumandartistlist = [None] * len(albumnames)

for i in range(len(albumnames)):
    if "," in artists[i].text:
        artist = get_first_part_before_comma(artists[i].text) + " various"
    else:
        artist = artists[i].text
    albumandartistlist[i] = " ".join([albumnames[i], artist])

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

    print("===============================================")
    print("---OVERALL PROGRESS--- >>> " , i * 100 / albumcount , "%")
    print("===============================================")

driver.quit()