from __future__ import annotations

import discord
from discord.ui import View, Select, Modal, TextInput, button, Button, select, ChannelSelect
from models import Configuration

class GuildsSelect(Select):
    def __init__(self, guilds: list[discord.Guild]) -> None:
        options: list[discord.SelectOption] = [discord.SelectOption(label=guild.name, value=str(guild.id)) for guild in guilds]

        super().__init__(custom_id="bububot:mutual", placeholder="Selecciona un servidor...", min_values=1, max_values=1, options=options, disabled=False, row=0)

    async def callback(self, interaction: discord.Interaction) -> None:
        value: int = int(self.values[0])

        cfg: Configuration = Configuration.filter(guild=value).get()

        if not cfg.enabled:
            await interaction.response.send_message('¡Este servidor no permite soporte vía MD! Inténtelo de nuevo.')
            return

        embed: discord.Embed = discord.Embed(
            description=cfg.message,
            color=discord.Color.random()
        )

        guild = interaction.client.get_guild(value)
        channel = guild.get_channel(cfg.channel)

        parent = await channel.create_thread(name=str(interaction.user.id), message=None, type=discord.ChannelType.private_thread, reason=f"Nuevo hilo de soporte de {interaction.user.id}", invitable=False)

        v: UserToGuildView = UserToGuildView(parent=parent)

        await interaction.response.edit_message(view=v, embed=embed)

class MutualGuilds(View):
    def __init__(self, author: discord.User) -> None:
        super().__init__(timeout=None)

        self.author: discord.User = author

        actual_guilds: list[discord.Guild] = []

        for guild in author.mutual_guilds:
            cfg = Configuration.filter(guild=guild.id).get_or_none()

            if cfg:
                actual_guilds.append(guild)

        self.add_item(GuildsSelect(actual_guilds))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.author.id

class _MessageModal(Modal):
    def __init__(self, *, guild: bool, object: discord.abc.Messageable, parent: discord.Thread) -> None:
        super().__init__(title="Envía un mensaje", timeout=180)
        self.object: discord.abc.Messageable = object
        self.parent: discord.abc.Messageable = parent
        self.is_guild: bool = guild

    msg: TextInput = TextInput(label='Mensaje', style=discord.TextStyle.long, placeholder='Tu mensaje...', required=True, row=0)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        embed: discord.Embed = discord.Embed(
            title=f"Mensaje de {interaction.user}",
            description=self.msg.value,
            color=interaction.user.color or interaction.user.accent_color or discord.Color.green()
        )

        if self.is_guild:
            await self.parent.send(embed=embed)
            await self.object.send(embed=embed, view=UserToGuildView(parent=self.parent))

        else:
            await self.object.send(embed=embed, view=GuildToUserView(user=interaction.user, parent=self.parent))

        await interaction.response.send_message('Tu mensaje se ha enviado', ephemeral=True)

class UserToGuildView(View):
    def __init__(self, *, parent: discord.Thread) -> None:
        super().__init__(timeout=None)
        self.parent: discord.Thread = parent

    @button(label='Responder', custom_id='bububot:utg:reply', disabled=False, style=discord.ButtonStyle.gray, row=0)
    async def button_callback(self, interaction: discord.Interaction, button: Button) -> None:
        button.disabled = True
        await interaction.edit_original_response(view=self)
        await interaction.response.send_modal(_MessageModal(guild=False, object=self.parent, parent=self.parent))
        self.stop()

class GuildToUserView(View):
    def __init__(self, *, user: discord.User, parent: discord.Thread) -> None:
        super().__init__(timeout=None)
        self.user: discord.User = user
        self.parent: discord.Thread = parent

    @button(label='Responder', custom_id='bububot:gtu:reply', disabled=False, style=discord.ButtonStyle.grey, row=0)
    async def button_callback(self, interaction: discord.Interaction, button: Button) -> None:
        button.disabled = True
        self.solved.disabled = True
        await interaction.edit_original_response(view=self)
        await interaction.response.send_modal(_MessageModal(guild=True, object=self.user, parent=self.parent))
        self.stop()

    @button(label='Marcar como resuelto', custom_id='bububot:gtu:solved', disabled=False, style=discord.ButtonStyle.green, row=1)
    async def solved(self, interaction: discord.Interaction, button: Button) -> None:
        button.disabled = True
        self.button_callback.disabled = True
        await interaction.edit_original_response(view=self)
        await interaction.response.send_message(f'Se ha marcado este hilo como resuelto por {interaction.user}, archivando...')

        await self.parent.edit(locked=True, archived=True)
        await self.user.send(embed=discord.Embed(title=f'Hilo marcado como resuelto por {interaction.user}', description=f'Tu hilo de soporte de {interaction.guild.name} se ha marcado como resuelto.\nPuede abrir otro enviando un mensaje por MDs a este bot.'))
        self.stop()

class ChangeMessageModal(Modal):
    def __init__(self, *, config: Configuration) -> None:
        super().__init__(title='Cambiar el mensaje', timeout=360*2)
        self.cfg: Configuration = config

        self.msg: TextInput = TextInput(label='Establece el nuevo mensaje', style=discord.TextStyle.long, placeholder='Bienvenido...', default=self.cfg.message, required=True)

        self.add_item(self.msg)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        self.cfg.message = self.msg.value
        await self.cfg.save()
        await interaction.response.send_message(f'Se ha cambiado el mensaje a:\n```\n{self.msg.value}```')

class ConfigurationView(View):
    def __init__(self, config: Configuration) -> None:
        self.config: Configuration = config
        super().__init__(timeout=360)

        if not self.config.enabled:
            self.disable_or_enable.label = 'Habilitar'
            self.disable_or_enable.style = discord.ButtonStyle.green

    async def on_timeout(self) -> None:
        for child in self.children:
            child.disabled = True

    @button(label='Deshabilitar', style=discord.ButtonStyle.red, row=0, disabled=False)
    async def disable_or_enable(self, interaction: discord.Interaction, button: Button) -> None:
        if button.label.lower() == 'deshabilitar':
            button.label = 'Habilitar'
            button.style = discord.ButtonStyle.green

        else:
            button.label = 'Deshabilitar'
            button.style = discord.ButtonStyle.red

        self.config.enabled = not self.config.enabled

        await self.config.save()

        await interaction.response.edit_message(view=self)

    @button(label='Cambiar mensaje', style=discord.ButtonStyle.blurple, row=0)
    async def change_message(self, interaction: discord.Interaction, _: Button) -> None:
        await interaction.response.send_modal(ChangeMessageModal(config=self.config))

    @select(cls=ChannelSelect, channel_types=[discord.ChannelType.text], placeholder='Elige el canal donde se crearan los hilos de soporte...', min_values=1, max_values=1, row=1)
    async def channels(self, interaction: discord.Interaction, select: ChannelSelect) -> None:
        channel = select.values[0]
        
        self.config.channel = channel.id
        
        await self.config.save()
        await interaction.response.send_message(f'Se ha establecido el canal de hilos de soporte a {channel.mention}')
