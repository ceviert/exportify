import io
import sys
from dotenv import load_dotenv
import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import ytmusicapi
import json

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
        print(f"Error fetching album ID: {e}")
        return None
    
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

plname = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "pl-name")))
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
    # print("-> " + album.encode('ascii', 'ignore').decode('ascii'))

albumcount = len(albumnames)

trackidelements = driver.find_elements(By.XPATH, '//*[@id="tracks-table"]/tbody/tr/td[22]')

trackids = []
i = 0
for element in trackidelements:
    trackids.append(element.text)

for trackid in trackids:
    time.sleep(0.5)
    # print("-> " + trackid)

namesandartists = []
i = 0
while i < songcount:
    full = artists[i].text + " - " + songnames[i].text
    namesandartists.append(full)
    i += 1
print("scrape DONE.")
time.sleep(2)

videoIdList = []

with open("songcache.json", "r") as file:
    loaded_data = json.load(file)

for song, trackid in zip(namesandartists, trackids):

    if trackid in loaded_data:
        print(song + " with track id " + trackid + " already cached.")
        videoId = loaded_data[trackid]

    else:
        ytm = ytmusicapi.YTMusic()
        query = song
        search_results = ytm.search(query)
        # print(search_results)
        for result in search_results:
            if isinstance(result, dict) and 'resultType' in result:
                if result['resultType'] == 'song' and result['category'] in ['Songs', 'Top result']:
                    print(f"Video ID: {result['videoId']}")
                    videoId = result['videoId']
                    break

    videoIdList.append(videoId)

for i, trackid in enumerate(trackids):
    if trackid not in loaded_data:
        loaded_data[trackid] = videoIdList[i]

with open("songcache.json", "w") as file:
    json.dump(loaded_data, file, indent=4)

end_time = time.time()
time_elapsed = end_time - start_time
print("Time elapsed => " + str(time_elapsed) + " seconds.")

driver.quit()