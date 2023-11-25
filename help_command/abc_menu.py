__all__ = ["EnhancedMenu"]

from abc import ABCMeta

import discord
from discord.ext import commands


class EnhancedMenu(metaclass=ABCMeta):
    """
    A base class for menus used with EnhancedHelpCommand
    """

    async def send_pages(
        self,
        ctx: commands.Context,
        destination: discord.abc.Messageable,
        pages: list[discord.Embed],
        *,
        reference: discord.Message
    ):
        """The function called by :cls:`EnhancedHelpCommand` that will send pages"""
        pass
