import discord, sys
sys.dont_write_bytecode = True
from discord.ext import commands
from src.connector import shared

class AppCMDListeners(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot) -> None:
        self.bot: commands.AutoShardedBot = bot

    @commands.Cog.listener()
    async def on_raw_app_command_permissions_update(self, payload: discord.RawAppCommandPermissionsUpdateEvent) -> None:
        shared.loop.create_task(shared.queue.add_to_queue(e="on_raw_app_command_permissions_update", guild_id=payload.guild.id, payload=payload))

    @commands.Cog.listener()
    async def on_app_command_completion(self, interaction: discord.Interaction, command: discord.app_commands.ContextMenu | discord.app_commands.Command) -> None:
        shared.loop.create_task(shared.queue.add_to_queue(e="on_app_command_completion", guild_id=interaction.guild.id, interaction=interaction, command=command))

async def setup(bot: commands.AutoShardedBot) -> None:
    await bot.add_cog(AppCMDListeners(bot))
