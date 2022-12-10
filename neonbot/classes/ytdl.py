from __future__ import annotations

import functools
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

import yt_dlp

from .ytdl_info import YtdlInfo
from .. import bot
from ..utils import log
from ..utils.exceptions import YtdlError


class Ytdl:
    def __init__(self, extra_params=None) -> None:
        if extra_params is None:
            extra_params = {}
        self.thread_pool = ThreadPoolExecutor()
        self.loop = bot.loop
        self.ytdl = yt_dlp.YoutubeDL(
            {
                "default_search": "ytsearch5",
                "format": "bestaudio/91/92/93/94/95/best/worst",
                "quiet": True,
                "nocheckcertificate": True,
                "ignoreerrors": True,
                "geo_bypass": True,
                "geo_bypass_country": "PH",
                "source_address": "0.0.0.0",
                "outtmpl": "./tmp/youtube_dl/%(id)s",
                "download_archive": "./tmp/youtube_dl/archive.txt",
                "compat_opts": {
                    "no-youtube-unavailable-videos": True
                },
                **extra_params,
            }
        )

    async def extract_info(self, keyword: str) -> Optional[YtdlInfo]:
        try:
            result = await self.loop.run_in_executor(
                self.thread_pool,
                functools.partial(
                    self.ytdl.extract_info, keyword, download=False, process=True
                ),
            )

            return YtdlInfo(result)
        except Exception as error:
            log.exception(error)
            raise YtdlError(error)

    async def process_entry(self, info: dict) -> Optional[YtdlInfo]:
        try:
            result = await self.loop.run_in_executor(
                self.thread_pool,
                functools.partial(self.ytdl.process_ie_result, info, download=not info.get('is_live')),
            )

            return YtdlInfo(result)
        except Exception as error:
            log.exception(error)
            raise YtdlError(error)

    @classmethod
    def create(cls, extra_params) -> Ytdl:
        return cls(extra_params)
