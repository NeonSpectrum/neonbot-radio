import re

from i18n import t

from neonbot.classes.ytdl import Ytdl
from neonbot.utils.constants import YOUTUBE_REGEX
from neonbot.utils.exceptions import YtdlError, YoutubeError


class Youtube:
    async def search_url(self, url: str):
        if not re.search(YOUTUBE_REGEX, url):
            raise YoutubeError(t('music.invalid_youtube_url'))

        try:
            ytdl_info = await Ytdl().extract_info(url)

            if ytdl_info.is_playlist:
                data, error = self.remove_invalid_videos(ytdl_info.get_list())
            else:
                data = ytdl_info.get_track()

            return data
        except YtdlError:
            raise YoutubeError(t('music.invalid_youtube_url'))

    def remove_invalid_videos(self, data):
        error = 0
        new_data = []

        for entry in data:
            if entry['title'] in ('[Private video]', '[Deleted video]'):
                error += 1
            else:
                new_data.append(entry)

        return new_data, error
