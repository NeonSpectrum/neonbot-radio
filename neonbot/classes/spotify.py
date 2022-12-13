import asyncio
from time import time
from typing import Optional
from urllib.parse import urlparse

from envparse import env
from i18n import t

from .ytdl import Ytdl
from .. import bot
from ..utils.exceptions import ApiError, YtdlError, SpotifyError


class Spotify:
    CREDENTIALS = {
        'token': None,
        'expiration': 0
    }
    BASE_URL = "https://api.spotify.com/v1"

    def __init__(self) -> None:
        self.client_id = env.str("SPOTIFY_CLIENT_ID")
        self.client_secret = env.str("SPOTIFY_CLIENT_SECRET")

        self.id = None
        self.type = None

    @property
    def url_prefix(self) -> str:
        if self.is_album:
            return '/albums'
        elif self.is_playlist:
            return '/playlists'
        else:
            return '/tracks'

    @property
    def is_playlist(self) -> str:
        return self.type == "playlist"

    @property
    def is_album(self) -> str:
        return self.type == "album"

    async def get_token(self) -> Optional[str]:
        if Spotify.CREDENTIALS['expiration'] and time() < Spotify.CREDENTIALS['expiration']:
            return Spotify.CREDENTIALS['token']

        res = await bot.session.post(
            f"https://{self.client_id}:{self.client_secret}@accounts.spotify.com/api/token",
            params={"grant_type": "client_credentials"},
            headers={
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        data = await res.json()

        if data.get('error_description'):
            raise ApiError(data['error_description'])

        Spotify.CREDENTIALS['token'] = data['access_token']
        Spotify.CREDENTIALS['expiration'] = time() + data['expires_in'] - 600

        return Spotify.CREDENTIALS['token']

    def parse_url(self, url: str) -> Optional[dict]:
        parsed = urlparse(url)
        scheme = parsed.scheme
        hostname = parsed.netloc
        path = parsed.path
        url_type = None
        url_id = None

        try:
            if hostname == "open.spotify.com" or "open.spotify.com" in path:
                url_type, url_id = path.split("/")[-2:]
            elif scheme == "spotify":
                url_type, url_id = path.split(":")
            if not url_type or not url_id:
                raise ValueError
        except ValueError:
            return None

        return dict(id=url_id, type=url_type)

    async def get_track(self) -> dict:
        return await self.request(self.url_prefix + '/' + self.id)

    async def get_playlist(self) -> list:
        playlist = []

        if self.type == "album":
            limit = 50
        else:
            limit = 100

        offset = 0

        while True:
            data = await self.request(
                self.url_prefix + "/" + self.id + '/tracks',
                params={"offset": offset, "limit": limit}
            )

            if 'items' not in data:
                break

            playlist += data['items']

            if data['next'] is None:
                break

            offset += limit

        return playlist

    async def request(self, url: str, params: dict = None):
        token = await self.get_token()

        res = await bot.session.get(
            Spotify.BASE_URL + url,
            headers={"Authorization": f"Bearer {token}"},
            params=params
        )

        return await res.json()

    async def search_url(self, url: str) -> None:
        url = self.parse_url(url)

        if not url:
            raise SpotifyError(t('music.invalid_spotify_url'))

        playlist = []

        self.id = url['id']
        self.type = url['type']

        if self.is_playlist or self.is_album:
            playlist = await self.get_playlist()
        else:
            playlist.append(await self.get_track())

        if len(playlist) == 0:
            raise SpotifyError(t('music.youtube_no_song'))

        data = await self.process_playlist(playlist)

        if len(data) == 0:
            raise SpotifyError(t('music.youtube_failed_to_find_similar'))

        return data

    async def get_playlist_info(self):
        uploader = None

        data = await self.request(
            self.url_prefix + '/' + self.id,
            params={
                'fields': 'name,external_urls,images,owner'
            }
        )

        if self.is_playlist:
            uploader = data.get('owner')['display_name']
        elif self.is_album:
            uploader = ', '.join(map(lambda artist: artist['name'], data.get('artists', [])))

        return dict(
            title=data.get('name'),
            url=data.get('external_urls')['spotify'],
            thumbnail=data.get('images')[0]['url'] if len(data.get('images')) > 0 else None,
            uploader=uploader,
        )

    async def process_playlist(self, playlist):
        async def search(item):
            ytdl_one = Ytdl.create({"default_search": "ytsearch1"})

            track = item['track'] if self.is_playlist else item

            try:
                ytdl_info = await ytdl_one.extract_info(
                    f"{' '.join(artist['name'] for artist in track['artists'])} {track['name']} lyric",
                )
            except YtdlError:
                return None

            ytdl_list = ytdl_info.get_list()

            if len(ytdl_list) == 0:
                return None

            return ytdl_list[0]

        data = await asyncio.gather(*[search(item) for item in playlist])

        return list(filter(None, data))
