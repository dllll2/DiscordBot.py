import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# Spotify API 클라이언트 ID와 시크릿 설정
client_id = "0b23902e1182453890fec42aa4020775"
client_secret = "8f33fe99c6e241a393dc02a1051f8ebf"

# 인증 관리자 설정
client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

# 노래 제목 입력
track_name = "눈이오잖아"

# 노래 검색
results = sp.search(q='track:' + track_name, type='track')

# 첫 번째 검색 결과에서 아티스트 이름 가져오기
track = results['tracks']['items'][0]
artist = track['artists'][0]['name']

print(f"Artist of '{track_name}': {artist}")