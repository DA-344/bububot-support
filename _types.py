from __future__ import annotations

from help_command import PrettyHelp

from tortoise import Tortoise

import discord
from discord import app_commands
from discord.ext.commands import Bot, Cog

class BubuBot(Bot):
    def __init__(self, *, cogs: list[Cog] | None = None) -> None:
        super().__init__("!", help_command=PrettyHelp(), description="Envíame un MD para recibir ayuda", intents=discord.Intents.all(),)
        self.bcogs: list[Cog] | None = cogs
        self.guild: discord.Object = discord.Object(id=1020800221451661433)

    async def setup_hook(self) -> None:
        await super().setup_hook()

        await Tortoise.init(db_url="sqlite://base.db", modules={'models': ['models']})
        await Tortoise.generate_schemas(safe=True)

        await self.load_extension('jishaku')

        if self.bcogs:
            for cog in self.bcogs:
                print(f"Inyectando el Cog {cog.qualified_name}...")
                await self.add_cog(cog(self))
                print("Inyectado correctamente...")
