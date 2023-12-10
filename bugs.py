import requests
import pandas as pd
from bs4 import BeautifulSoup
import yt_dlp
from concurrent.futures import ThreadPoolExecutor
import time
from selenium import webdriver

# 드라이버 열기
options = webdriver.ChromeOptions()
options.add_argument('--headless')  # 화면 표시 없이 실행 (Headless 모드)
driver = webdriver.Chrome(options=options)
driver.maximize_window()

# 벅스 차트에서 곡 제목과 아티스트 가져오기
url = 'https://music.bugs.co.kr/chart'
driver.get(url)
html = driver.page_source
soup = BeautifulSoup(html, 'html.parser')

# 벅스는 곡 제목이 'p' 태그의 'title' 클래스로 되어있습니다.
song_titles = [title.get_text().strip() for title in soup.find_all('p', class_='title')[:10]]
# 아티스트는 'p' 태그의 'artist' 클래스로 되어있습니다.
artists = [artist.get_text().strip() for artist in soup.find_all('p', class_='artist')[:10]]

def get_youtube_url(title, artist):
    try:
        search_query = f"{title} {artist} official music video"  # Create a search query combining title and artist
        ydl_opts = {
            'default_search': 'ytsearch',
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(search_query, download=False)
            return info_dict['entries'][0]['webpage_url']
    except Exception as e:
        print(f"Error finding URL for '{title} - {artist}': {e}")
        return None

# 멀티스레딩으로 유튜브 URL 가져오기
with ThreadPoolExecutor(max_workers=5) as executor:
    youtube_urls = list(executor.map(get_youtube_url, song_titles, artists))

# 드라이버 종료
driver.quit()

# 노래 제목, 아티스트, 유튜브 URL 출력
for i, (title, artist, url) in enumerate(zip(song_titles, artists, youtube_urls)):
    print(f"{i+1}. {title} - {artist} - {url}")
