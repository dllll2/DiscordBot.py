import requests
import pandas as pd
from bs4 import BeautifulSoup
import yt_dlp
from concurrent.futures import ThreadPoolExecutor
import time
from selenium import webdriver

# 드라이버 열기
options = webdriver.ChromeOptions()
options.add_argument('--headless')  # 화면 표시 없이 실행 (헤드리스 모드)
driver = webdriver.Chrome(options=options)
driver.maximize_window()

# 페이지 로딩을 위한 대기 시간 설정
# driver.implicitly_wait(10)

# 지니 차트에서 곡 제목과 아티스트 가져오기
url = 'https://www.genie.co.kr/chart/top200'
driver.get(url)
html = driver.page_source
soup = BeautifulSoup(html, 'html.parser')

songs = soup.select('tr.list')
song_info = []

for song in songs[:10]:  # 상위 10곡
    song_title = song.select_one('td.info a.title').get_text(strip=True)
    song_artist = song.select_one('td.info a.artist').get_text(strip=True)
    song_info.append((song_title, song_artist))

def get_youtube_url(song_info):
    song_title, song_artist = song_info
    try:
        ydl_opts = {
            'default_search': 'ytsearch',
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(f'{song_title} - {song_artist}', download=False)
            return info_dict['entries'][0]['webpage_url']
    except Exception as e:
        print(f"'{song_title} - {song_artist}' 곡에 대한 URL을 찾는 중 오류 발생: {e}")
        return None

# 멀티스레딩으로 유튜브 URL 가져오기
with ThreadPoolExecutor(max_workers=5) as executor:
    youtube_urls = list(executor.map(get_youtube_url, song_info))

# 드라이버 종료
driver.quit()

# 노래 제목과 유튜브 URL 출력
for i, ((title, artist), url) in enumerate(zip(song_info, youtube_urls)):
    print(f"{i+1}. {title} - {artist} - {url}")
