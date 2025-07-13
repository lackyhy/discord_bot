import discord
import asyncio

from discord.ext import commands
from discord import app_commands

from ast import alias
from youtubesearchpython import VideosSearch
from yt_dlp import YoutubeDL

from libs import lbs

class music_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
        #all the music related stuff
        self.is_playing = False
        self.is_paused = False

        # 2d array containing [song, channel]
        self.music_queue = []
        self.YDL_OPTIONS = {'format': 'bestaudio/best'}
        self.FFMPEG_OPTIONS = {'options': '-vn'}

        self.vc = None
        self.ytdl = YoutubeDL(self.YDL_OPTIONS)

     #searching the item on youtube
    def search_yt(self, item):
        if item.startswith("https://"):
            title = self.ytdl.extract_info(item, download=False)["title"]
            return{'source':item, 'title':title}
        search = VideosSearch(item, limit=1)
        return{'source':search.result()["result"][0]["link"], 'title':search.result()["result"][0]["title"]}

    async def play_next(self):
        if len(self.music_queue) > 0:
            self.is_playing = True

            #get the first url
            m_url = self.music_queue[0][0]['source']

            #remove the first element as you are currently playing it
            self.music_queue.pop(0)
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(m_url, download=False))
            song = data['url']
            self.vc.play(discord.FFmpegPCMAudio(song, executable= "ffmpeg.exe", **self.FFMPEG_OPTIONS), after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(), self.bot.loop))
        else:
            self.is_playing = False

    # infinite loop checking 
    async def play_music(self, ctx):
        if len(self.music_queue) > 0:
            self.is_playing = True

            m_url = self.music_queue[0][0]['source']
            #try to connect to voice channel if you are not already connected
            if self.vc == None or not self.vc.is_connected():
                self.vc = await self.music_queue[0][1].connect()

                #in case we fail to connect
                if self.vc == None:

                    await send_message(interaction, "```Could not connect to the voice channel```", True)
                    return
            else:
                await self.vc.move_to(self.music_queue[0][1])
            #remove the first element as you are currently playing it
            self.music_queue.pop(0)
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(m_url, download=False))
            song = data['url']
            self.vc.play(discord.FFmpegPCMAudio(song, executable= "ffmpeg", **self.FFMPEG_OPTIONS), after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(), self.bot.loop))

        else:
            self.is_playing = False


    @app_commands.command(name="play", description="Plays a selected song from YouTube")
    @app_commands.describe(query="The search query or URL of the song to play")
    async def play(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()

        voice_channel = None
        if interaction.user.voice and interaction.user.voice.channel:
            voice_channel = interaction.user.voice.channel
        else:
            await interaction.followup.send("``````")
            return

        if self.is_paused:
            self.vc.resume()
            await interaction.followup.send("Resumed the music.")
        else:
            song = self.search_yt(query)
            if type(song) == type(True):
                await interaction.followup.send("``````")
            else:
                if self.is_playing:
                    await interaction.followup.send(f"**#{len(self.music_queue)+2} - '{song['title']}'** added to the queue")
                else:
                    await interaction.followup.send(f"**'{song['title']}'** added to the queue")
                self.music_queue.append([song, voice_channel])
                if not self.is_playing:
                    await self.play_music(interaction)

    @app_commands.command(name="pause", description="Pauses the current song being played")
    async def pause(self, interaction: discord.Interaction):
        if self.is_playing:
            self.is_playing = False
            self.is_paused = True
            if self.vc and self.vc.is_playing():
                self.vc.pause()
            await interaction.response.send_message("Music paused.")
        elif self.is_paused:
            self.is_paused = False
            self.is_playing = True
            if self.vc and self.vc.is_paused():
                self.vc.resume()
            await lbs.send_message(interaction, "Music resumed.", True)
        else:
            await lbs.send_message(interaction, "No music is currently playing or paused.", True)

    @app_commands.command(name="resume", description="Resumes playing with the discord bot")
    async def resume(self, interaction: discord.Interaction):
        if self.is_paused:
            self.is_paused = False
            self.is_playing = True
            if self.vc and self.vc.is_paused():
                self.vc.resume()
            await lbs.send_message(interaction, "Music resumed.", True)
        else:
            await lbs.send_message(interaction, "Music is not paused.", True)

    @app_commands.command(name="skip", description="Skips the current song being played")
    async def skip(self, interaction: discord.Interaction):
        if self.vc and self.vc.is_playing():
            self.vc.stop()
            # Play next song if exists
            await self.play_music(interaction)
            await lbs.send_message(interaction, f"Skipped current song. author: {interaction.user}")
        else:
            await lbs.send_message(interaction, "No song is currently playing.")

    @app_commands.command(name="queue", description="Displays the current songs in queue")
    async def queue(self, interaction: discord.Interaction):
        if len(self.music_queue) == 0:
            await lbs.send_message(interaction, "No music in queue.", True)
            return

        retval = ""
        for i, song_data in enumerate(self.music_queue, start=1):
            retval += f"#{i} - {song_data[0]['title']}\n"

        await lbs.send_message(interaction, retval)


    @app_commands.command(name="stop", description="Kick the bot from voice channel")
    async def stop(self, interaction: discord.Interaction):
        self.is_playing = False
        self.is_paused = False
        if self.vc and self.vc.is_connected():
            await self.vc.disconnect()
            await lbs.send_message(interaction, "Disconnected from voice channel.", True)
        else:
            await lbs.send_message(interaction, "Bot is not connected to a voice channel.", True)

    @app_commands.command(name="remove", description="Removes last song added to queue")
    async def remove(self, interaction: discord.Interaction):
        if len(self.music_queue) > 0:
            removed_song = self.music_queue.pop()
            await lbs.send_message(interaction, f"Removed last song from queue: **{removed_song[0]['title']}**")
        else:
            await lbs.send_message(interaction, "Queue is empty, nothing to remove.")

async def setup(bot):
	await bot.add_cog(music_cog(bot))