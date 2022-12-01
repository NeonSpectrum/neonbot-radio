from datetime import timedelta
from typing import Union

import discord


def get_command_string(interaction: discord.Interaction):
    params = []

    # Context menu starts with uppercase
    if interaction.command.name[0].isupper():
        try:
            users = list(interaction.data['resolved']['users'].values())
            params = [f"{user['username']}#{user['discriminator']}" for user in users]
        except IndexError:
            pass
    else:
        params = [
            f'{key}="{value}"'
            for key, value in interaction.namespace.__dict__.items()
        ]

    return f"{interaction.command.name} {' '.join(params)}"


def format_seconds(secs: Union[int, float]) -> str:
    formatted = str(timedelta(seconds=secs)).split(".")[0]
    if formatted.startswith("0:"):
        return formatted[2:]
    return formatted
