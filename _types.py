from __future__ import annotations

from help_command import PrettyHelp

import discord
from discord import app_commands
from discord.ext.commands import Bot

class BubuBot(Bot):
    def __init__(self) -> None:
        super().__init__("!", help_command=PrettyHelp(), tree_cls=app_commands.CommandTree(self), description="Envíame un MD para recibir ayuda", intents=discord.Intents.all(),)
