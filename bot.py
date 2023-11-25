from __future__ import annotations

import discord
from discord.ext.commands import Cog
from _types import BubuBot
from env import TOKEN

bot = BubuBot()

@bot.event
async def on_ready() -> None:
    print(f"Conectado como {bot.user}")
    print(f"Observando a {len(list(bot.get_all_members()))}")
