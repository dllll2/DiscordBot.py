import selenium
from selenium import webdriver
import time
import pandas as pd
from bs4 import BeautifulSoup
import requests
from itertools import repeat

# 크롬드라이버 열기
driver = webdriver.Chrome()
driver.maximize_window() # 크롬창 크기 최대

time.sleep(2)

# 드라이버가 해당 url 접속
url = 'https://www.melon.com/chart/index.htm' # 멜론차트 페이지
driver.get(url)

html = driver.page_source # 드라이버 현재 페이지의 html 정보 가져오기 
                            
soup = BeautifulSoup(html, 'lxml')

# 멜론 차트에서 곡 제목을 가져오기 (10개만)
song_titles = []
for title in soup.find_all('div', attrs={'class': 'ellipsis rank01'})[:10]:
    song_titles.append(title.find('a').get_text())

# 가져온 곡 제목 출력
for i, title in enumerate(song_titles):
    print(f"{i+1}. {title}")
