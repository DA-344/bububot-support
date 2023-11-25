from __future__ import annotations

import logging

from typing import Literal

import discord
from discord.ext.commands import is_owner
from discord.ext.commands import Context

from _types import BubuBot
from env import TOKEN
from cogs import Config

bot = BubuBot(cogs=[Config,])

@bot.event
async def on_ready() -> None:
    print(f"Conectado como {bot.user}")
    print(f"Observando a {len(list(bot.get_all_members()))} miembros")

@bot.event
async def on_message(message: discord.Message) -> None:
    if message.content.startswith(bot.command_prefix):
        try:
            await bot.process_commands(message)
        except:
            pass

    if not message.guild:
        ...

@bot.command(hidden=True)
@is_owner()
async def sync(ctx: Context, *, guild: Literal["^", "~"] = "~") -> None:
    r"""Sincroniza los comandos de barra diagonal a este o a todos los servidores.

    Argumentos
    ----------
    guild: '^' | '~'
        Los servidores a los que sincronizar los comandos. `^` para todos los servidores y `~` para este.
    """
    clean_guild: discord.Guild | None = ctx.guild if guild == "~" else None

    synced = await bot.tree.sync(guild=clean_guild)
    await ctx.reply(f"Se han sincronizado {len(synced)} comandos en {'este servidor' if guild == '~' else f'{len(bot.guilds)} servidor(es)'}", delete_after=60)

bot.run(TOKEN, log_level=logging.DEBUG)
