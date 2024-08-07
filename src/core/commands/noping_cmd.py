import discord, sys
sys.dont_write_bytecode = True
from discord.ext import commands
from src.connector import shared

from src.core.helpers.modals import ModalHelper
from src.core.helpers.embeds import create_base_embed

from xRedUtils.type_hints import SIMPLE_ANY, BUILTINS

class NoPing(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot) -> None:
        self.bot: commands.AutoShardedBot = bot

        self.troubleshooter: dict[str, str] = {
            "status": "Bot is **disabled**. Make sure to enable it in `General` settings",
            "staffRole": "Missing **staff/mod role.**",
            "staffChannel": "Missing **staff/mod text channel.**",
            "adminRole": "Missing **administrator role.**",
            "adminChannel": "Missing **administrator text channel.**"
        }
    
    async def report(self, option: str, components: list[dict], interaction: discord.Interaction) -> None:        
        if option == "bug" and (report_channel := self.bot.get_channel(1234544223236260010)):
            embed = create_base_embed("Bug report", description=f"**Error ID:** `{ID if (ID := components["txt_err_id"]) else "No ID provided"}`\n**Affected component:** {components["txt_component"]}")
            embed.add_field(name="`` Description: ``", value=components["txt_desc"], inline=False)
            embed.add_field(name="`` Reproduction steps: ``", value=components["txt_rep_steps"], inline=False)
            embed.add_field(name="`` Other: ``", value=other if (other := components["txt_other"]) else "No data provided.", inline=False)
        
        elif option == "feedback" and (report_channel := self.bot.get_channel(1235577391620034661)):
            embed = create_base_embed("Feedback", description=f"**Name:** {components["txt_name"]}")
            embed.add_field(name="`` Description: ``", value=components["txt_desc"], inline=False)
            embed.add_field(name="`` Other: ``", value=other if (other := components["txt_other"]) else "No data provided.", inline=False)
        
        if embed and report_channel:
            embed.set_footer(text=f"{interaction.user.display_name} ({interaction.user.id}) in {interaction.guild.name} ({interaction.guild_id})")
            await report_channel.send(embed=embed)
    
    async def handle_modal(self, interaction: discord.Interaction, option: str, text_inputs: list[discord.ui.TextInput]) -> None:
        modal = ModalHelper(f"{option.capitalize()} report:", custom_id="NOPING_CMD:MDL")
        for input in text_inputs:
            modal.add_item(input)

        await interaction.response.send_modal(modal)
        response: dict = await modal.clean_data()
        interaction: discord.Interaction = response.get("interaction")
        components: dict[str, str] = response.get("components")

        if interaction and components:
            await interaction.followup.send(content=f"Thank you for submitting a {option} report! Developer has been notified.", ephemeral=True)
            await self.report(option, components, interaction)
        else:
            await interaction.followup.send(content=f"An unknown error has occured.", ephemeral=True)

    @discord.app_commands.choices(cmd=[
        discord.app_commands.Choice(name="help", value="help"),
        discord.app_commands.Choice(name="ping", value="ping"),
        discord.app_commands.Choice(name="troubleshoot", value="trouble"),
        discord.app_commands.Choice(name="feedback", value="feedback"),
        discord.app_commands.Choice(name="report_bug", value="bug"),
    ])
    @discord.app_commands.command(name="noping", description="General/Info command of NoPing")
    async def noping(self, interaction: discord.Interaction, cmd: discord.app_commands.Choice[str], args: str = None) -> None:
        if cmd.value == "help":
            embed: discord.Embed = create_base_embed("Help page")
            embed.add_field(name="Quick Start", value=f"__Due to security standards, only **guild owner** ({interaction.guild.owner.display_name}) can configure bot.__\
                            \nOwner can **grant/rewoke** configuration permissions to **everyone** with `Administrator guild permission` using **</admin_editing:1235708858580860928>** slash command. \
                            \n\nBy default, Bot is **disabled** and will have to be **enabled** in `General settings` using **</config:1235708858580860929>** slash command.\
                            \nBot also requires a couple of general settings to be set. They are required and bot will **NOT** work without them. Required settings have `REQUIRED` tag in their descriptions.", inline=False)
            embed.add_field(name="─────────────────────────────────────────────────────────────", value="**Navigation:**\
                            \nUse arrows to navigate, `✕` for stopping configuration.\
                            \n- `❔ > `Displays general information about that plugin.\n- `⚙️ > `Starts the configurator for that plugin.\
                            \n**Read** instructions of the `Configuration Wizard` for plugin specific setup/configuration.\
                            \n\n**General:**\
                            \n - You have **1 hour** to configure each time you execute **</config:1235708858580860929>** command. You will be notified if that time is reached.\n- Please **read** instructions, they are important.\n- Each plugin has its own `switch`, meaning you can disable them anytime for whatever reason.\
                            \nFor any questions and concerns, feel free to create **feedback or bug report** using **</noping:1235708858136002623>** command, or join the [Support Server](https://discord.gg/gzx3kxu68x)", inline=False)

            await interaction.response.send_message(embed=embed, ephemeral=True)
        elif cmd.value == "ping":
            await interaction.response.send_message(f"Pong! Running on {round(self.bot.latency * 1000)}ms.", ephemeral=True)
        elif cmd.value == "bug":
            text_inputs: list[discord.TextInput] = [
                discord.ui.TextInput(label="Error ID:", custom_id="txt_err_id", placeholder="Enter error ID if it was provided. This field is not required.", required=False, max_length=36),
                discord.ui.TextInput(label="Component/Part:", custom_id="txt_component", style=discord.TextStyle.long, max_length=100, placeholder="Write which component/plugin/command is affected by the bug. Example: 'ping protection on xyz rule'"),
                discord.ui.TextInput(label="Description", custom_id="txt_desc", max_length=1000, style=discord.TextStyle.long, placeholder="In depth explaination of the bug. Provide as much details as possible."),
                discord.ui.TextInput(label="Reproduction steps:", custom_id="txt_rep_steps", max_length=1000, style=discord.TextStyle.long, placeholder="Steps to trigger/create the bug."),
                discord.ui.TextInput(label="Other:", custom_id="txt_other", style=discord.TextStyle.long, max_length=1000, placeholder="Other information. Can be anything, not required.", required=False)
            ]
            await self.handle_modal(interaction, cmd.value, text_inputs)
        elif cmd.value == "feedback":
            text_inputs: list[discord.TextInput] = [
                discord.ui.TextInput(label="Name:", custom_id="txt_name", placeholder="Name of the idea/feedback/change", max_length=50),
                discord.ui.TextInput(label="Description", custom_id="txt_desc", max_length=1000, style=discord.TextStyle.long, placeholder="In depth explaination of the feedback. Provide as much details as possible."),
                discord.ui.TextInput(label="Other:", custom_id="txt_other", style=discord.TextStyle.long, max_length=1000, placeholder="Other information. Can be anything, not required.", required=False)
            ]
            await self.handle_modal(interaction, cmd.value, text_inputs)

        elif cmd.value == "trouble":
            guild_db: dict[str, SIMPLE_ANY] = shared.db.load_data(interaction.guild.id)
            embed: discord.Embed = create_base_embed(title="Troubleshooter")

            # checking required settings
            general_settings: dict[str, BUILTINS] = guild_db.get("general")

            # checking plugin settings

async def setup(bot: commands.AutoShardedBot) -> None:
    await bot.add_cog(NoPing(bot))