import re

from i18n import t

from neonbot import bot
from neonbot.classes.embed import Embed
from neonbot.classes.player import Player
from neonbot.classes.with_interaction import WithInteraction
from neonbot.classes.ytdl import Ytdl
from neonbot.utils.constants import YOUTUBE_REGEX
from neonbot.utils.exceptions import YtdlError


class Youtube(WithInteraction):
    async def send_message(self, *args, **kwargs):
        await bot.send_response(self.interaction, *args, **kwargs)

    async def search_url(self, url: str):
        if not re.search(YOUTUBE_REGEX, url):
            await self.send_message(embed=Embed(t('music.invalid_youtube_url')), ephemeral=True)
            return

        player = await Player.get_instance(self.interaction)

        try:
            ytdl_info = await Ytdl().extract_info(url)

            if ytdl_info.is_playlist:
                data, error = self.remove_invalid_videos(ytdl_info.get_list())
            else:
                data = ytdl_info.get_track()

            player.add_to_queue(data)
        except YtdlError:
            await self.send_message(embed=Embed(t('music.no_songs_available')))

    def remove_invalid_videos(self, data):
        error = 0
        new_data = []

        for entry in data:
            if entry['title'] in ('[Private video]', '[Deleted video]'):
                error += 1
            else:
                new_data.append(entry)

        return new_data, error
