from __future__ import annotations

import logging

import discord

from _types import BubuBot
from env import TOKEN
from cogs import Config
from views import MutualGuilds

bot = BubuBot(cogs=[Config,])

@bot.event
async def on_ready() -> None:
    print(f"Conectado como {bot.user}")
    print(f"Observando a {len(list(bot.get_all_members()))} miembros")

@bot.event
async def on_message(message: discord.Message) -> None:
    if message.author.bot or message.author == bot.user:
        return
    
    if message.content.startswith(bot.command_prefix):
        try:
            await bot.process_commands(message)
        except:
            pass

    if not message.guild:
        await message.reply(
            f"¡Hola, {message.author.mention}! Elige el servidor con el que quieres contactar:",
            view=await MutualGuilds.init(message.author)
        )

bot.run(TOKEN, log_level=logging.DEBUG)
