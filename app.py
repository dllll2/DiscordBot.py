import asyncio
from distutils.core import gen_usage
import discord
import yt_dlp as youtube_dl
from discord.ext import commands
from dico_token import Token
import requests
import melon  # melon.py를 import
import genie
import bugs
import lyricsgenius as lg

from discord.ui import View, Select

# Genius 웹사이트에서 발급받은 API 토큰을 입력해주세요
genius = lg.Genius("2u60zKRY7dhhecD9uoVdY8AEi23_znsMTd4z1Kz8TSapOTrO44KJ0CtZMJsFqLkhjz2-wXp8AePEzE1SrsrZUA")


ytdl_format_options = {
    'format': 'bestaudio/best',                           #오디오품질 최상4
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',  #다운로드된 파일의 이름및 경로
    'restrictfilenames': True,                            #파일 이름에 공백 사용 x
    'noplaylist': True,                                   #플레이리스트를 가져오지않는다
    'nocheckcertificate': True,                           #SSL인증서의 유효성 확인
    'ignoreerrors': False,                                #오류 발생시 다운로드 중단
    'logtostderr': False,                                 
    'quiet': True,                                        #작업 완료 메시지를 출력X
    'no_warnings': True,                                  #경고메시지 출력X
    'default_search': 'auto',                             #기본 검색 엔진 설정
    'source_address': '0.0.0.0',                          
}

#ffmpeg: 동영상을 재생할때 쓰이는 코덱.
ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', #-reconnect 1: 스트리밍 중에 연결이 끊겼을 때 재연결을 시도하도록 지정. '1'은 재연결을 시도하는 최대 횟수를 나타냄
                                                                                   #-reconnect_streamed 1: 스트림으로부터 데이터를 다운로드할 때 재연결을 시도하도록 지정합니다.
                                                                                   #-reconnect_delay_max 5: 재연결 시도 간의 최대 지연 시간을 초 단위로 지정합니다. 여기서 '5'는 5초를 나타냅니다.
    'options': '-vn',                                                              #FFmpeg이 오디오 스트림만을 처리하도록 지정. '-vn'은 비디오 스트림을 무시하도록 설정하는 옵션
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.genius = lg.Genius("rIYeS-Peg3TWuV0E_DW5sxDepbxr_kxsuaqHB3lXHfmG4toHzS2CSP-IVTY0tiZ4")  # Genius API 키로 초기화

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = []


    async def play_next(self, ctx):
        if self.queue:
            self.queue.pop(0)  # 현재 재생 중인 곡을 큐에서 삭제

        if self.queue:
            next_song = self.queue[0]
            
            player = await YTDLSource.from_url(next_song['url'], loop=self.bot.loop, stream=True)
            ctx.voice_client.play(player, after=lambda e: self.bot.loop.create_task(self.play_next(ctx)))





    @commands.command()
    async def join(self, ctx, *, channel: discord.VoiceChannel):
        """음성채널 입장"""

        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)

        await channel.connect()

    

    @commands.command()
    async def play(self, ctx, *, url):
        """!play <노래제목> 입력한 노래를 재생합니다."""

        if ctx.voice_client is None:
            await self.join(ctx, channel=ctx.author.voice.channel)

        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            data = player.data

            duration_seconds = data['duration']
            if duration_seconds < 3600:
                duration_formatted = f"{duration_seconds // 60}:{duration_seconds % 60}"
            else:
                duration_formatted = f"{duration_seconds // 3600}:{(duration_seconds % 3600) // 60}:{duration_seconds % 60}"

            # 대기열에 노래 추가
            self.queue.append(data)

            queue_index = len(self.queue)

            await ctx.send(f"노래 제목: {url}")



            # 재생 중인 노래가 없는 경우 노래를 바로 재생
            if not ctx.voice_client.is_playing() and len(self.queue) == 1:
                ctx.voice_client.play(player, after=lambda e: self.bot.loop.create_task(self.play_next(ctx)))
                embed = discord.Embed(title=data['title'])
                embed.add_field(name="상태", value="바로 재생", inline=True)
                embed.add_field(name="곡 길이", value=duration_formatted, inline=True)
                embed.add_field(name="음원", value=f"[YouTube Link]({data['webpage_url']})", inline=True)
                embed.set_footer(text=ctx.author.display_name)
                embed.set_thumbnail(url=data['thumbnail'])
                await ctx.send(embed=embed)
            else:
                # 대기열에 추가된 노래 정보를 표시
                embed = discord.Embed(title=data['title'])
                embed.add_field(name="곡 길이", value=duration_formatted, inline=True)
                embed.add_field(name="대기", value=f"Queue position: {queue_index}", inline=True)
                embed.add_field(name="음원", value=f"[YouTube Link]({data['webpage_url']})", inline=True)
                embed.set_footer(text=ctx.author.display_name)
                embed.set_thumbnail(url=data['thumbnail'])
                await ctx.send(embed=embed)
                await ctx.send(f"재생목록 추가: {data['title']} (대기번호: {queue_index})")

    

    @commands.command()
    async def pause(self, ctx):
        """현재 재생중인 노래 일시정지"""

        if not ctx.voice_client or not ctx.voice_client.is_playing():
            return await ctx.send("일시정지할 노래가 없어요!")

        # 현재 재생중인 노래 일시정지
        ctx.voice_client.pause()

        await ctx.send("노래를 일시정지 했어요 !resume 를 입력하여 노래를 다시 재생할 수 있어요.")

    @commands.command()
    async def resume(self, ctx):
        """일시정지된 오래 다시 재생"""

        if not ctx.voice_client or not ctx.voice_client.is_paused():
            return await ctx.send("일시정지된 노래가 없어요!")

        # 일시정지된 노래 재생
        ctx.voice_client.resume()

        await ctx.send("일시정지된 노래를 다시 재생합니다.")

    @commands.command()
    async def stop(self, ctx):
        """모든 노래를 정지하고 음성채널 퇴장"""

        if ctx.voice_client is not None:
            #현재 재생중인 노래 정지
            ctx.voice_client.stop()

            #대기열 초기화
            self.queue.clear()

            #음성채널 퇴장
            await ctx.voice_client.disconnect()

            await ctx.send("모든노래를 정지하고 음성채널을 퇴장했습니다.")
        else:
            await ctx.send("음성채널에 연결되어 있지 않습니다.")    

        await ctx.voice_client.disconnect()

    @commands.command()
    async def queue(self, ctx):
        """대기열을 보여줌"""

        if not self.queue:
            return await ctx.send("재생목록이 비어있어요!!")

        queue_list = "\n".join([f"{i + 1}. {song['title']}" for i, song in enumerate(self.queue)])
        embed = discord.Embed(title="Music Queue")
        embed.description = queue_list
        await ctx.send(embed=embed)

    @commands.command()
    async def skip(self, ctx):
        """현재 재생중인 노래를 스킵하고 다음 큐의 노래를 가져옴"""

        if not ctx.voice_client:
            return await ctx.send("스킵할 노래가 없어요!")

        if not self.queue:
            return await ctx.send("다음 곡이 없어요!")

        # 현재 재생중인 노래 정지
        ctx.voice_client.stop()

        # 현재 재생중인 노래 queue에서 삭제
        current_song = self.queue.pop(0)

        # queue에서 다음노래 가져옴
        if self.queue:
            next_song = self.queue[0]

            # 다음 노래 재생
            player = await YTDLSource.from_url(next_song['url'], loop=self.bot.loop, stream=True)
            ctx.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)

            duration_seconds = next_song['duration']
            if duration_seconds < 3600:
                duration_formatted = f"{duration_seconds // 60}:{duration_seconds % 60}"
            else:
                duration_formatted = f"{duration_seconds // 3600}:{(duration_seconds % 3600) // 60}:{duration_seconds % 60}"

            # 다음 노래의 정보 표시
            embed = discord.Embed(title=next_song['title'])
            embed.add_field(name="상태", value="다음 곡 재생", inline=True)
            embed.add_field(name="곡 길이", value=duration_formatted, inline=True)
            embed.add_field(name="음원", value=f"[YouTube Link]({next_song['webpage_url']})", inline=True)
            embed.set_footer(text=ctx.author.display_name)
            embed.set_thumbnail(url=next_song['thumbnail'])
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"Skipped: {current_song['title']}. ")

    @commands.command()
    async def put(self, ctx, position: int, *, url):
        """대기열의 특정 위치에 노래를 삽입합니다."""

        if position < 1 or position > len(self.queue) + 1:
            return await ctx.send(f"1부터 {len(self.queue) + 1} 사이의 숫자를 입력해주세요.")

        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            data = player.data

            # 대기열에 노래 삽입
            self.queue.insert(position - 1, data)

            await ctx.send(f"{data['title']}이(가) 대기열의 {position}번 위치에 추가되었습니다.")



    @commands.command()
    async def remove(self, ctx, *, arg):
        """대기열에서 특정 노래를 삭제합니다."""
        if not self.queue:
            return await ctx.send("대기열이 비어있습니다.")

        if arg == "all":
            self.queue.clear()
            return await ctx.send("대기열이 모두 삭제되었습니다.")

        # 범위 삭제 (예: "1-3")
        if '-' in arg:
            try:
                start, end = map(int, arg.split('-'))
                if start <= end and 1 <= start <= len(self.queue):
                    del self.queue[start-1:end]
                    return await ctx.send(f"{start}번부터 {end}번까지의 노래가 대기열에서 삭제되었습니다.")
                else:
                    return await ctx.send("잘못된 범위입니다.")
            except ValueError:
                return await ctx.send("올바른 숫자 범위를 입력해주세요.")

        # 단일 노래 삭제
        try:
            pos = int(arg)
            if 1 <= pos <= len(self.queue):
                del self.queue[pos-1]
                return await ctx.send(f"{pos}번 노래가 대기열에서 삭제되었습니다.")
            else:
                return await ctx.send("잘못된 숫자입니다.")
        except ValueError:
            return await ctx.send("올바른 숫자를 입력해주세요.")
    
    @commands.command()
    async def melonchart(self, ctx):
        """실시간 멜론차트 top10 재생"""

        if ctx.voice_client is None:
            await self.join(ctx, channel=ctx.author.voice.channel)

        async with ctx.typing():
            # melon.py에서 youtube_urls 가져오기
            youtube_urls = melon.youtube_urls

            for url in youtube_urls:
                player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True) #해당 url에 해당하는 동영상을 재생할수이쓴 player객체 생성
                data = player.data #player.data를 호출해서 플레이어의 데이터를 저장

                # 대기열에 노래 추가
                self.queue.append(data)

            # 대기열 초기화 및 첫 번째 곡 재생
            if not ctx.voice_client.is_playing() and len(self.queue) > 0: #재생중이 아니면
                next_song = self.queue.pop(0) #대기열의 젤 앞에있는 노래를 nextsong에 저장
                player = await YTDLSource.from_url(next_song['url'], loop=self.bot.loop, stream=True) #nextsong의 url을 사용하여 재생하는 player객체 생성
                ctx.voice_client.play(player, after=lambda e: self.bot.loop.create_task(self.play_next(ctx))) #노래재생생

                duration_seconds = next_song['duration']
                if duration_seconds < 3600:
                    duration_formatted = f"{duration_seconds // 60}:{duration_seconds % 60}"
                else:
                    duration_formatted = f"{duration_seconds // 3600}:{(duration_seconds % 3600) // 60}:{duration_seconds % 60}"

                embed = discord.Embed(title=next_song['title'])
                embed.add_field(name="상태", value="바로 재생", inline=True)
                embed.add_field(name="곡 길이", value=duration_formatted, inline=True)
                embed.add_field(name="음원", value=f"[YouTube Link]({next_song['webpage_url']})", inline=True)
                embed.set_footer(text=ctx.author.display_name)
                embed.set_thumbnail(url=next_song['thumbnail'])
                await ctx.send(embed=embed)
            else:
                await ctx.send("멜론 차트의 곡이 대기열에 추가되었습니다.")


    @commands.command()
    async def geinechart(self, ctx):
        """실시간 지니차트 top10 재생"""

        if ctx.voice_client is None:
            await self.join(ctx, channel=ctx.author.voice.channel)

        async with ctx.typing():
            # genie.py에서 youtube_urls 가져오기
            youtube_urls = genie.youtube_urls

            for url in youtube_urls:
                player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
                data = player.data

                # 대기열에 노래 추가
                self.queue.append(data)

            # 대기열 초기화 및 첫 번째 곡 재생
            if not ctx.voice_client.is_playing() and len(self.queue) > 0:
                next_song = self.queue.pop(0)
                player = await YTDLSource.from_url(next_song['url'], loop=self.bot.loop, stream=True)
                ctx.voice_client.play(player, after=lambda e: self.bot.loop.create_task(self.play_next(ctx)))

                duration_seconds = next_song['duration']
                if duration_seconds < 3600:
                    duration_formatted = f"{duration_seconds // 60}:{duration_seconds % 60}"
                else:
                    duration_formatted = f"{duration_seconds // 3600}:{(duration_seconds % 3600) // 60}:{duration_seconds % 60}"

                embed = discord.Embed(title=next_song['title'])
                embed.add_field(name="상태", value="바로 재생", inline=True)
                embed.add_field(name="곡 길이", value=duration_formatted, inline=True)
                embed.add_field(name="음원", value=f"[YouTube Link]({next_song['webpage_url']})", inline=True)
                embed.set_footer(text=ctx.author.display_name)
                embed.set_thumbnail(url=next_song['thumbnail'])
                await ctx.send(embed=embed)
            else:
                await ctx.send("지니 차트의 곡이 대기열에 추가되었습니다.")


    @commands.command()
    async def bugschart(self, ctx):
        """실시간 벅스차트 top10 재생"""

        if ctx.voice_client is None:
            await self.join(ctx, channel=ctx.author.voice.channel)

        async with ctx.typing():
            # bugs.py에서 youtube_urls 가져오기
            youtube_urls = bugs.youtube_urls

            for url in youtube_urls:
                player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
                data = player.data

                # 대기열에 노래 추가
                self.queue.append(data)

            # 대기열 초기화 및 첫 번째 곡 재생
            if not ctx.voice_client.is_playing() and len(self.queue) > 0:
                next_song = self.queue.pop(0)
                player = await YTDLSource.from_url(next_song['url'], loop=self.bot.loop, stream=True)
                ctx.voice_client.play(player, after=lambda e: self.bot.loop.create_task(self.play_next(ctx)))

                duration_seconds = next_song['duration']
                if duration_seconds < 3600:
                    duration_formatted = f"{duration_seconds // 60}:{duration_seconds % 60}"
                else:
                    duration_formatted = f"{duration_seconds // 3600}:{(duration_seconds % 3600) // 60}:{duration_seconds % 60}"

                embed = discord.Embed(title=next_song['title'])
                embed.add_field(name="상태", value="바로 재생", inline=True)
                embed.add_field(name="곡 길이", value=duration_formatted, inline=True)
                embed.add_field(name="음원", value=f"[YouTube Link]({next_song['webpage_url']})", inline=True)
                embed.set_footer(text=ctx.author.display_name)
                embed.set_thumbnail(url=next_song['thumbnail'])
                await ctx.send(embed=embed)
            else:
                await ctx.send("벅스 차트의 곡이 대기열에 추가되었습니다.")

    # @commands.command()
    # async def repeat(self, ctx):
    #     """현재 재생 중인 노래를 반복 재생합니다."""
    #     if not ctx.voice_client or not ctx.voice_client.is_playing():
    #         return await ctx.send("현재 재생 중인 노래가 없습니다.")

    #     self.is_repeating = not self.is_repeating
    #     status = "활성화" if self.is_repeating else "비활성화"
    #     await ctx.send(f"반복 모드가 {status}되었습니다.")


    
    import lyricsgenius as lg

    genius = lg.Genius("rIYeS-Peg3TWuV0E_DW5sxDepbxr_kxsuaqHB3lXHfmG4toHzS2CSP-IVTY0tiZ4")  # Genius API 키로 초기화

    @commands.command()
    async def lyrics(self, ctx, title: str = None, artist: str = None):
        """제공된 노래 제목과 아티스트로 가사를 검색합니다. 아티스트 정보가 없으면 제목만으로 검색합니다."""

        if not title:
            await ctx.send("사용 방법: `!lyrics <노래 제목> [아티스트 이름]`\n예시: `!lyrics Shape of You Ed Sheeran`")

        # 아티스트 이름이 제공되지 않았을 경우의 처리
        if not artist:
            song = genius.search_song(title)
            warning_msg = "⚠ 아티스트 정보가 없어 검색 결과가 정확하지 않을 수 있습니다."
        else:
            song = genius.search_song(title, artist)
            warning_msg = ""

        if song:
            lyrics = song.lyrics
            # Discord 임베드 생성
            embed = discord.Embed(title=f"**{title}** by **{artist or '알 수 없는 아티스트'}**", description=warning_msg, color=discord.Color.blue())
            # 가사가 긴 경우 여러 임베드로 나누어 전송
            while lyrics:
                # Discord 임베드의 설명란은 최대 2048자를 지원합니다
                if len(lyrics) > 2048:
                    embed.description += lyrics[:2048]
                    lyrics = lyrics[2048:]
                else:
                    embed.description += lyrics
                    lyrics = ""

                await ctx.send(embed=embed)
                embed = discord.Embed(color=discord.Color.blue())  # 새 임베드 준비
        else:
            # 가사를 찾을 수 없는 경우
            embed = discord.Embed(title=f"**{title}** by **{artist or '알 수 없는 아티스트'}**", description="가사를 찾을 수 없습니다.", color=discord.Color.red())
            await ctx.send(embed=embed)



intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix=commands.when_mentioned_or("!"),
    description='Relatively simple music bot example',
    intents=intents,
)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')


async def main():
    async with bot:
        await bot.add_cog(Music(bot))
        await bot.start(Token)

asyncio.run(main())
