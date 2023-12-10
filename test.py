import lyricsgenius as lg

# Genius 웹사이트에서 발급받은 API 토큰을 입력해주세요
genius = lg.Genius("2u60zKRY7dhhecD9uoVdY8AEi23_znsMTd4z1Kz8TSapOTrO44KJ0CtZMJsFqLkhjz2-wXp8AePEzE1SrsrZUA")

# 가사를 가져올 노래와 아티스트를 지정합니다.
artist_name = ""
song_title = "눈이오잖아"

# 해당 노래의 가사를 가져옵니다.
song = genius.search_song(song_title, artist_name)
if song is not None:
    print(song.lyrics)
else:
    print("가사를 찾을 수 없습니다.")