__all__ = ["AppMenu", "AppNav"]

import discord
from discord import Embed, Message
from discord.abc import Messageable
from discord.ext import commands
from discord.ext.commands import Context
from discord.ui import Select, View

from .abc_menu import EnhancedMenu


class AppNav(View):
    """
    The actual View for controlling the menu interaction.

    Args:
    -----
    pages: Optional[List[:cls:`Embed`]]
        The list of pages to cycle through. Defaults to None.

    timeout: Optional[:cls:`float`]
        The duration the interaction will be active for. Defaults to None.

    ephemeral: Optional[:cls:`bool`]
        Send as an ephemeral message. Defaults to False.
    """

    index: int = 0

    def __init__(
        self,
        pages: list[discord.Embed] | None = None,
        timeout: float | None = None,
        ephemeral: bool = False,
        allowed_user: discord.Member | None = None,
    ) -> None:
        super().__init__(timeout=timeout)

        self.page_count: int | None = len(pages) if pages else None
        self.pages: list[discord.Embed] | None = pages
        self.allowed_user: discord.Member | None = allowed_user

        if pages and len(pages) == 1:
            self.remove_item(self.previous)
            self.remove_item(self.next_)
            self.remove_item(self.select)

        if ephemeral:
            self.remove_item(self._delete)

        if pages and len(pages) > 1:
            for index, page in enumerate(pages):
                self.select.add_option(
                    label=page.title,
                    description=f"{page.description[:69]}".replace("`", ""),
                    value=index,
                )

    @discord.ui.button(
        label="Anterior",
        style=discord.ButtonStyle.success,
        row=1,
        custom_id="pretty_help:previous",
    )
    async def previous(
        self, interaction: discord.Interaction, button: discord.Button
    ) -> None:
        self.index -= 1
        await self.update(interaction)

    @discord.ui.button(
        label="Siguiente",
        style=discord.ButtonStyle.primary,
        row=1,
        custom_id="pretty_help:next",
    )
    async def next_(
        self, interaction: discord.Interaction, button: discord.Button
    ) -> None:
        self.index += 1
        await self.update(interaction)

    @discord.ui.button(
        label="Borrar",
        style=discord.ButtonStyle.danger,
        row=1,
        custom_id="pretty_help:delete",
    )
    async def _delete(
        self, interaction: discord.Interaction, button: discord.Button
    ) -> None:
        try:
            await interaction.message.delete()
        except Exception:
            await interaction.response.send_message(
                "No se pudo borrar el mensaje, inténtelo más tarde.", ephemeral=True
            )

    @discord.ui.select(row=2, custom_id="pretty_help:select")
    async def select(self, interaction: discord.Interaction, select: Select) -> None:
        self.index = int(select.values[0])
        await self.update(interaction)

    async def update(self, interaction: discord.Interaction) -> None:
        await interaction.response.edit_message(
            embed=self.pages[self.index % self.page_count], view=self
        )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if (
            not self.allowed_user
            and interaction.data.get("custom_id") == self._delete.custom_id
        ):
            return True
        return interaction.user == self.allowed_user


class AppMenu(EnhancedMenu):
    """
    Navigate pages using the Discord UI components.

    This menu can be *partially* persisntent with `client.add_view(AppMenu())`
    This will allow the delete button to work on past messages

    Args:
    -----
        timeout: Optional[:cls:`float`]
            The timeout. Defaults to None.

        ephemeral: :cls:`bool`
            Whether message should be ephemeral. Defaults to False.
    """

    # src: https://github.com/CasuallyCalm/discord-pretty-help/blob/master/pretty_help/app_menu.py

    def __init__(self, timeout: float | None = None, ephemeral: bool = False) -> None:
        self.timeout: float | None = timeout
        self.ephemeral: bool = ephemeral

    async def send_pages(
        self,
        ctx: Context,
        destination: Messageable | None,
        pages: list[Embed],
        *,
        reference: Message | None = None,
    ):
        if ctx.interaction:
            await ctx.interaction.response.send_message(
                embed=pages[0],
                view=AppNav(
                    pages=pages,
                    timeout=self.timeout,
                    ephemeral=self.ephemeral,
                    allowed_user=ctx.author,
                ),
                ephemeral=self.ephemeral,
            )

        else:
            if not destination and not reference:
                raise ValueError("Both destination and reference are null")

            if not destination:
                await reference.reply(
                    embed=pages[0],
                    view=AppNav(
                        pages=pages, timeout=self.timeout, allowed_user=ctx.author
                    ),
                )

            elif not reference:
                await destination.send(
                    embed=pages[0],
                    view=AppNav(
                        pages=pages, timeout=self.timeout, allowed_user=ctx.author
                    ),
                )
