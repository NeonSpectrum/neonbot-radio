from __future__ import annotations

from typing import Any, Optional

import discord


class Embed(discord.Embed):
    def __init__(self, description: Any = None, **kwargs: Any) -> None:
        if description is not None:
            super().__init__(description=description and str(description).strip(), **kwargs)
        else:
            super().__init__(**kwargs)
        self.color = 0xE91E63

    def add_field(self, name: Any, value: Any, *, inline: bool = True) -> Embed:
        super().add_field(name=name, value=value, inline=inline)
        return self

    def set_author(
        self,
        name: str,
        url: str = None,
        *,
        icon_url: str = None,
    ) -> Embed:
        super().set_author(name=name, url=url, icon_url=icon_url)
        return self

    def set_footer(
        self, text: str = None, *, icon_url: str = None
    ) -> Embed:
        super().set_footer(text=text, icon_url=icon_url)
        return self

    def set_image(self, url: str) -> Embed:
        if url:
            super().set_image(url=url)
        return self

    def set_thumbnail(self, url: Optional[str]) -> Embed:
        if url:
            super().set_thumbnail(url=url)
        return self
