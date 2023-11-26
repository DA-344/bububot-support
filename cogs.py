from __future__ import annotations

import discord
from discord.ext.commands import Cog, hybrid_group as group, Context as Ctx, guild_only
from discord.app_commands import guild_only as app_guild_only

from _types import BubuBot
from views import ConfigurationView
from models import Configuration

@guild_only()
@app_guild_only()
class Config(Cog, name="Configuración"):
    r"""Comandos de configuración para servidores.
    """

    def __init__(self, bot: BubuBot) -> None:
        self.client: BubuBot = bot

    @group(name='support')
    async def support(self, _: Ctx) -> None:
        pass

    @support.command(name='setup')
    async def setup(self, ctx: Ctx) -> None:
        """Configura tu servidor o cambia la configuración ya disponible"""
        cfg: Configuration | None = await Configuration.filter(guild=ctx.guild.id).get_or_none()

        if not cfg:
            cfg = Configuration(
                guild=ctx.guild.id,
                enabled=True
            )

        await ctx.reply(embed=discord.Embed(title=f"Configuración de soporte de {ctx.guild.name}"), view=ConfigurationView(ctx.author, cfg))
