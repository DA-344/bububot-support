from __future__ import annotations

from help_command import PrettyHelp

import discord
from discord import app_commands
from discord.ext.commands import Bot, Cog

class BubuBot(Bot):
    def __init__(self, *, cogs: list[Cog] | None = None) -> None:
        super().__init__("!", help_command=PrettyHelp(), tree_cls=app_commands.CommandTree(self), description="Envíame un MD para recibir ayuda", intents=discord.Intents.all(),)
        self.cogs: list[Cog] | None = cogs
        self.guild: discord.Object = discord.Object(id=1020800221451661433)

    async def setup_hook(self) -> None:
        await super().setup_hook()

        if self.cogs:
            for cog in self.cogs:
                print(f"Inyectando el Cog {cog.qualified_name}...")
                await self.add_cog(cog(self))
                print("Inyectado correctamente...")
