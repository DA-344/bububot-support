__all__: list[str] = ["PrettyHelp", "Paginator"]

from random import randint
from typing import Optional

import discord

from discord import app_commands
from discord.ext import commands
from discord.ext.commands.context import Context
from discord.ext.commands.help import HelpCommand

from .abc_menu import EnhancedMenu
from .app_menu import AppMenu


class Paginator:
    """A class that creates pages for Discord messages.

    Attributes
    -----------
    prefix: Optional[:class:`str`]
        The prefix inserted to every page. e.g. three backticks.
    suffix: Optional[:class:`str`]
        The suffix appended at the end of every page. e.g. three backticks.
    max_size: :class:`int`
        The maximum amount of codepoints allowed in a page.
    color: Optional[:class:`discord.Color`, :class: `int`]
        The color of the discord embed. Default is a random color for every invoke
    ending_note: Optional[:class:`str`]
        The footer in of the help embed
    image_url: Optional[:class:`str`]
        The url of the image to be used on the embed
    thumbnail_url: Optional[:class:`str`]
        The url of the thumbnail to be used on the embed
    """

    def __init__(
        self,
        show_index: bool,
        color: discord.Color = 0,
        image_url: str | None = None,
        thumbnail_url: str | None = None,
    ) -> None:
        self.char_limit: int = 6000
        self.color: discord.Color = color
        self.ending_note: str = ""
        self.field_limit: int = 25
        self.image_url: str | None = image_url
        self.prefix: str = "```"
        self.suffix: str = "```"
        self.show_index: bool = show_index
        self.thumbnail_url: str | None = thumbnail_url
        self.clear()

    def clear(self) -> None:
        """Clears the paginator to have no pages"""
        self._pages: list[discord.Embed] = []

    def _check_embed(self, embed: discord.Embed, *chars: str):
        """
        Check if the embed is too big to be sent on discord

        Args:
            embed (discord.Embed): The embed to check

        Returns:
            bool: Will return True if the embed isn't too large
        """
        return (
            len(embed) + sum(len(char) for char in chars if char) < self.char_limit
            and len(embed.fields) < self.field_limit
        )

    def _new_page(self, title: str, description: str):
        """
        Create a new page

        Args:
            title (str): The title of the new page

        Returns:
            discord.Embed: Returns an embed with the title and color set
        """
        embed = discord.Embed(title=title, description=description, color=self.color)
        embed.set_image(url=self.image_url)
        embed.set_thumbnail(url=self.thumbnail_url)
        return embed

    def _add_page(self, page: discord.Embed):
        """
        Add a page to the paginator

        Args:
            page (discord.Embed): The page to add
        """
        page.set_footer(text=self.ending_note)
        self._pages.append(page)

    def add_cog(
        self, title: str | commands.Cog, commands_list: list[commands.Command]
    ) -> None:
        """
        Add a cog page to the help menu
        """

        cog = isinstance(title, commands.Cog)

        if not commands_list:
            return

        page_title = title.qualified_name if cog else title
        embed = self._new_page(page_title, (title.description or "") if cog else "")

        self._add_command_fields(embed, page_title, commands_list)

    def _add_command_fields(
        self,
        embed: discord.Embed,
        page_title: str,
        command_list: list[commands.Command | app_commands.Command],
        group: bool = False,
    ):
        """
        Adds command fields to Category/Cog and Command Group pages.
        """

        for command in command_list:
            command_name = command.qualified_name
            if group or isinstance(command, commands.Group):
                command_name = "[`+`]" + command_name

            if isinstance(command, commands.Command):
                short_doc = command.short_doc

            else:
                short_doc = command.description.split("\n", 1)[0]

            if not self._check_embed(
                embed,
                self.ending_note,
                command_name,
                short_doc,
                self.prefix,
                self.suffix,
            ):
                self._add_page(embed)
                embed = self._new_page(page_title, embed.description)

            embed.add_field(
                name=command_name,
                value=f"{self.prefix}{short_doc or 'Sin descripción corta'}{self.suffix}",
                inline=False,
            )

        self._add_page(embed)

    @staticmethod
    def __command_info(command: commands.Command | commands.Group) -> str:
        info: str = ""
        if command.description:
            info += command.description + "\n\n"

        if command.help:
            info += command.help

        if not info:
            info = "Ninguna"

        return info

    def add_app_command(
        self, command: app_commands.commands.Command, signature: str
    ) -> None:
        """
        Add an app command to the help page
        """

        page = self._new_page(
            command.name, f"{self.prefix}{command.description}{self.suffix}"
        )
        page.add_field(
            name="Uso", value=f"{self.prefix}{signature}{self.suffix}", inline=False
        )

        page.add_field(name="Parámetros:", value="⠀", inline=False)

        for parameter in sorted(
            command.parameters, key=lambda x: (not x.required, x.name)
        ):
            if parameter.description:
                description = (
                    "" if parameter.description == "..." else parameter.description
                )

                page.add_field(
                    name=parameter.name,
                    value=f"```Obligatorio: {'Sí' if parameter.required else 'No'}\n{description}```",
                    inline=False,
                )

        self._add_page(page)

    def add_app_group(self, group: app_commands.commands.Group, signature: str) -> None:
        """
        Add an app command to the help page
        """

        page = self._new_page(
            group.qualified_name, f"{self.prefix}{group.description}{self.suffix}"
        )

        self._add_command_fields(page, group.name, group.walk_commands(), group=True)

    def add_command(self, command: commands.Command, signature: str):
        """
        Add a command help page
        """

        page = self._new_page(
            command.qualified_name,
            f"{self.prefix}{self.__command_info(command)}{self.suffix}" or "",
        )

        if command.aliases:
            aliases: str = ", ".join(command.aliases)

            page.add_field(
                name="Alias", value=f"{self.prefix}{aliases}{self.suffix}", inline=False
            )

        if cooldown := command._buckets._cooldown:
            page.add_field(
                name="Congelamiento",
                value=f"{cooldown.rate} {'vez' if cooldown.rate == 1 else 'veces'} cada {cooldown.per} segundo{'s' if cooldown.per != 1 else ''}",
            )

        page.add_field(
            name="Uso", value=f"{self.suffix}{signature}{self.suffix}", inline=False
        )

        self._add_page(page)

    def add_group(
        self, group: commands.Group, commands_list: list[commands.Command]
    ) -> None:
        """
        Add a group help page

        Args:
            group (commands.Group): The command group to get help for
            commands_list (List[commands.Command]): The list of commands in the group
        """
        page = self._new_page(
            group.name, f"{self.prefix}{self.__command_info(group)}{self.suffix}" or ""
        )

        self._add_command_fields(page, group.name, commands_list, group=True)

    def add_index(self, title: str, bot: commands.Bot) -> None:
        """
        Add an index page to the response of the bot_help command

        Args:
            title (str): The title of the index page
            bot (commands.Bot): The bot instance
        """
        if self.show_index:
            index = self._new_page(title, bot.description or "")

            for page_no, page in enumerate(self._pages, 1):
                index.add_field(
                    name=f"{page_no}) {page.title}",
                    value=f'{self.prefix}{page.description or "Sin descripción"}{self.suffix}',
                    inline=False,
                )
            index.set_footer(text=self.ending_note)
            self._pages.insert(0, index)
        else:
            self._pages[0].description = bot.description

    @property
    def pages(self) -> list[discord.Embed] | list:
        """Returns the rendered list of pages."""
        if len(self._pages) == 1:
            return self._pages
        lst = []
        start = 0 if self.show_index else 1
        pages = len(self._pages) - 1 if self.show_index else len(self._pages)
        for page_no, page in enumerate(self._pages, start):
            page: discord.Embed
            if not self.show_index or page_no != 0:
                page.description = f"`Página: {page_no}/{pages}`\n{page.description}"
            lst.append(page)
        return lst


class PrettyHelp(HelpCommand, commands.Cog):
    """The implementation of the prettier help command.
    A more refined help command format
    This inherits from :class:`HelpCommand`.
    It extends it with the following attributes.

    Attributes
    ------------

    case_insensitive: :class: `bool`
        Ignore case when searching for commands ie 'HELP' --> 'help' Defaults to ``False``.
    color: :class: `discord.Color`
        The color to use for the help embeds. Default is a random color.
    delete_invoke: Optional[:class:`bool`]
        Delete the message that invoked the help command. Requires message delete permission.
        Defaults to ``False``.
    dm_help: Optional[:class:`bool`]
        A tribool that indicates if the help command should DM the user instead of
        sending it to the channel it received it from. If the boolean is set to
        ``True``, then all help output is DM'd. If ``False``, none of the help
        output is DM'd. If ``None``, then the bot will only DM when the help
        message becomes too long (dictated by more than :attr:`dm_help_threshold` characters).
        Defaults to ``False``.
    ending_note: Optional[:class:`str`]
        The footer in of the help embed
    image_url: Optional[:class:`str`]
        The url of the image to be used on the embed
    index_title: :class: `str`
        The string used when the index page is shown. Defaults to ``"Categories"``
    menu: Optional[:class:`pretty_help.PrettyMenu`]
        The menu to use for navigating pages. Default is :class:`pretty_help.DefaultMenu`
        Custom menus should inherit from :class:`pretty_help.PrettyMenu`
    no_category: :class:`str`
        The string used when there is a command which does not belong to any category(cog).
        Useful for i18n. Defaults to ``"No Category"``
    paginator: :class: `pretty_help.Paginator`
        The paginator to use. One is created by default.
    send_typing: :class: `bool`
        A bool that indicates if the bot will send a typing indicator. Defaults to ``True``
    show_index: class: `bool`
        A bool that indicates if the index page should be shown listing the available cogs
        Defaults to ``True``.
    sort_commands: :class:`bool`
        Whether to sort the commands in the output alphabetically. Defaults to ``True``.
    thumbnail_url: Optional[:class:`str`]
        The url of the thumbnail to be used on the embed
    """

    def __init__(
        self,
        case_insensitive: bool = False,
        color: discord.Color = discord.Color.from_rgb(
            randint(0, 255), randint(0, 255), randint(0, 255)
        ),
        delete_invoke: bool = False,
        dm_help: bool = False,
        ending_note: str = "",
        image_url: str | None = None,
        index_title: str = "Categorías",
        menu: EnhancedMenu = AppMenu(),
        no_category: str = "Sin categoría",
        paginator: Paginator | None = None,
        send_typing: bool = True,
        show_index: bool = True,
        sort_commands: bool = True,
        thumbnail_url: str | None = None,
        **options,
    ) -> None:
        self.dm_help: bool = dm_help
        self.index_title: str = index_title
        self.no_category: str = no_category
        self.sort_commands: bool = sort_commands
        self.menu: EnhancedMenu = menu
        self.paginator: Paginator = paginator or Paginator(
            show_index=show_index,
            color=color,
            image_url=image_url,
            thumbnail_url=thumbnail_url,
        )
        self.case_insensitive: bool = case_insensitive
        self.ending_note: str = ending_note
        self.delete_invoke: bool = delete_invoke
        self.send_typing: bool = send_typing

        super().__init__(**options)

    def _add_to_bot(self, bot: commands.Bot) -> None:
        super()._add_to_bot(bot)
        self.bot: commands.Bot = bot
        bot.tree.add_command(self._app_command_callback)

    def _remove_from_bot(self, bot: commands.Bot) -> None:
        super()._remove_from_bot(bot)
        bot.tree.remove_command(self._app_command_callback.name)

    @app_commands.describe(
        command="El comando, grupo o subcomandos del que obtener ayuda"
    )
    @app_commands.command(name="help")
    async def _app_command_callback(
        self, interaction: discord.Interaction, command: str | None = None
    ) -> None:
        """
        Obtén ayuda del bot o de los comandos.
        """

        bot: commands.Bot = interaction.client
        ctx: commands.Context = await commands.Context.from_interaction(interaction)
        ctx.bot: commands.Bot = bot
        await ctx.invoke(bot.get_command("help"), command=command)

    @_app_command_callback.autocomplete("command")
    async def __help_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        cmds: list[str] = [cmd.qualified_name for cmd in self.bot.walk_commands()]

        cmds += [
            app_cmd.name
            for app_cmd in self.bot.tree.get_commands(
                type=discord.AppCommandType.chat_input, guild=interaction.guild
            )
        ]

        cmds = sorted(cmds, key=lambda x: x.lower())

        return [
            app_commands.Choice(name=cmd, value=cmd)
            for cmd in cmds
            if current.lower() in cmd.lower()
        ][:24]

    async def filter_app_commands(
        self, app_command: list[app_commands.AppCommand], sort: bool = True
    ) -> list[app_commands.AppCommand]:
        """Filter App commands and optionally sort them"""
        if sort:
            app_command.sort(key=lambda x: x.name)

        return app_command

    async def prepare_help_command(
        self, ctx: Context, command: commands.Command
    ) -> None:
        self.context: commands.Context = ctx
        if ctx.guild is not None:
            perms = ctx.channel.permissions_for(ctx.guild.me)

            if not perms.embed_links:
                raise commands.BotMissingPermissions(("embed links",))

            if not perms.read_message_history:
                raise commands.BotMissingPermissions(("read message history",))

            if not perms.add_reactions:
                raise commands.BotMissingPermissions(["add reactions"])

        self.paginator.clear()
        self.paginator.ending_note = self.get_ending_note()
        await super().prepare_help_command(ctx, command)

    async def command_callback(
        self, ctx: Context, /, *, command: str | None = None
    ) -> None:
        await self.prepare_help_command(ctx, command)

        if command is not None:
            keys: list[str] = command.split(" ")
            bot: commands.Bot = ctx.bot

            if cmd := bot.tree.get_command(keys[0]):
                for key in keys[1:]:
                    try:
                        found = cmd.get_command(key)

                    except AttributeError:
                        pass

                    else:
                        cmd = found

                if isinstance(cmd, app_commands.commands.Group):
                    await self.send_app_group_help(cmd)

                else:
                    await self.send_app_command_help(cmd)

                return

        await super().command_callback(ctx, command=command)

    def get_ending_note(self):
        note = self.ending_note or (
            "Escribe {help.clean_prefix}{help.invoked_with} <comando> para obtener más información de un comando\n"
            "También puedes escribir {help.clean_prefix}{help.invoked_with} <categoría> para obtener más información de una categoría."
        )

        return note.format(
            ctx=self.context,
            help=self if hasattr(self, "clean_prefix") else self.context,
        )

    async def send_pages(self):
        pages = self.paginator.pages
        destination = self.get_destination()

        if self.delete_invoke and self.context.interaction is None:
            try:
                await self.context.message.delete()

            except (discord.errors.Forbidden, commands.errors.CommandInvokeError):
                print("Missing permissions to delete invoked message")

        if not pages:
            await destination.send(f"```{self.get_ending_note()}```")

        else:
            await self.menu.send_pages(self.context, destination, pages)

    async def send_bot_help(self, mapping: dict):
        bot: commands.Bot = self.context.bot
        channel = self.get_destination()
        app_mapping = list(
            filter(
                lambda cmd: isinstance(cmd, app_commands.commands.Command)
                and not isinstance(cmd, commands.hybrid.HybridAppCommand)
                and cmd.name != "help",
                bot.tree.get_commands(),
            )
        )

        if self.send_typing:
            await channel.typing()

        mapping = {name: [] for name in mapping}

        help_filtered = (
            filter(lambda c: c.name != "help", bot.commands)
            if len(bot.commands) > 1
            else bot.commands
        )

        for cmd in (
            await self.filter_commands(help_filtered, sort=self.sort_commands)
            + app_mapping
        ):
            if hasattr(cmd, "binging"):
                mapping[cmd.binding].append(cmd)

            else:
                mapping[cmd.cog].append(cmd)

        self.paginator.add_cog(self.no_category, mapping.pop(None))
        sorted_map = sorted(
            mapping.items(),
            key=lambda cg: cg[0].qualified_name
            if isinstance(cg[0], commands.Cog)
            else str(cg[0]),
        )

        for cog, cmd_list in sorted_map:
            if cog.app_command:
                cmd_list += cog.app_command.commands

            self.paginator.add_cog(cog, cmd_list)

        self.paginator.add_index(self.index_title, bot)
        await self.send_pages()

    def get_app_command_signature(self, command: app_commands.commands.Command):
        """
        Returns the application command signature

        Args:
            command (app_commands.commands.Command): The Application command to get a signature for
        """
        required = ""
        not_required = ""
        if command.parameters:
            required = " ".join(
                f"<{parameter.name}>"
                for parameter in command.parameters
                if parameter.required
            )
            not_required = " ".join(
                f"[{parameter.name}]"
                for parameter in command.parameters
                if not parameter.required
            )

        return f"/{command.qualified_name} {required} {not_required}"

    def get_app_group_signature(self, group: app_commands.commands.Group):
        """
        Returns the application command group signature

        Args:
            group (app_commands.commands.Group): The Application group to get a signature for
        """
        return f"/{group.qualified_name}"

    async def send_app_command_help(self, command: app_commands.commands.Command):
        self.paginator.add_app_command(command, self.get_app_command_signature(command))
        await self.send_pages()

    async def send_app_group_help(self, group: app_commands.commands.Group):
        self.paginator.add_app_group(group, self.get_app_group_signature(group))
        await self.send_pages()

    async def send_command_help(self, command: commands.Command):
        filtered = await self.filter_commands([command])
        if filtered:
            self.paginator.add_command(command, self.get_command_signature(command))
            await self.send_pages()

    async def send_group_help(self, group: commands.Group):
        if self.send_typing:
            await self.get_destination().typing()
        filtered = await self.filter_commands(group.commands, sort=self.sort_commands)
        self.paginator.add_group(group, filtered)
        await self.send_pages()

    async def send_cog_help(self, cog: commands.Cog):
        if self.send_typing:
            await self.get_destination().typing()
        filtered = await self.filter_commands(
            cog.get_commands(), sort=self.sort_commands
        )
        filtered += await self.filter_app_commands(cog.get_app_commands())
        if cog.app_command:
            filtered += await self.filter_app_commands(cog.app_command.commands)
        self.paginator.add_cog(cog, filtered)
        await self.send_pages()

    async def send_error_message(self, error: str, /) -> None:
        """Check if the context is from an app command or text command and send an error message"""
        if self.context.interaction:
            return await self.context.interaction.response.send_message(
                error, ephemeral=True
            )

        return await super().send_error_message(error)
