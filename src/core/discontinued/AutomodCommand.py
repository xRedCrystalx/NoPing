import discord, sys
sys.dont_write_bytecode = True
from discord.ext import commands
from discord import app_commands
import src.connector as con

class AutomodCommand(commands.GroupCog, name="automod"):
    def __init__(self, bot: commands.Bot) -> None:
        self.shared: con.Shared = con.shared
        self.bot: commands.Bot = bot

    @app_commands.command(name = "load_rules", description = "Loads all automod modules.")
    async def load(self, interaction: discord.Interaction) -> None:
        BotData: dict = self.shared.db.load_data(interaction.guild.id)
        
        embed_list: list[discord.Embed] = []
        def replace_symbols(strs: list[str]) -> list[str]:
            newList: list[str] = [x.replace("*", "\\*").replace("_", "\\_").replace("`", "\\`").replace("@", "\\@") for x in strs]
            return newList

        if interaction.user.guild_permissions.administrator or interaction.user.id in [x for x in BotData["owners"]]:
            for rule in await interaction.guild.fetch_automod_rules():
                trigger: discord.AutoModTrigger = rule.trigger
                newEmbed: discord.Embed = discord.Embed(title=rule.name, description=f"- **Rule ID:** {rule.id}\n- **Status:**: `{'Enabled' if rule.enabled is True else 'Disabled'}`\n- **Type:** {trigger.type}", color=0xff0000)

                if trigger.type == discord.AutoModRuleTriggerType.keyword:
                    newEmbed.add_field(name="Keyword filter:", value=f"{', '.join(replace_symbols(trigger.keyword_filter)) if trigger.keyword_filter != [] else 'No filter keywords found.'}", inline=False)
                    regex: str = '\n- '.join(f"`{x}`" for x in trigger.regex_patterns)
                    newEmbed.add_field(name="Regex Patterns:", value=f"{regex if trigger.regex_patterns != [] else 'No regexes found.'}", inline=False)
                    newEmbed.add_field(name="Allowed words:", value=f"{', '.join(replace_symbols(trigger.allow_list)) if trigger.allow_list != [] else 'No allowed words found.'}", inline=False)

                elif trigger.type == discord.AutoModRuleTriggerType.spam:
                    pass

                elif trigger.type == discord.AutoModRuleTriggerType.keyword_preset:
                    newEmbed.add_field(name="Pre-Sets:", value=f"- Profanity: `{trigger.presets.profanity}`\n- Slurs: `{trigger.presets.slurs}`\n- Sexual Content: `{trigger.presets.sexual_content}`", inline=False)
                    newEmbed.add_field(name="Allowed words", value=f"{', '.join(replace_symbols(trigger.allow_list)) if trigger.allow_list != [] else 'No allowed words found.'}", inline=False)

                elif trigger.type == discord.AutoModRuleTriggerType.mention_spam:
                    newEmbed.add_field(name="Menton Spam Limit:", value=f"Max mentions per message: {trigger.mention_limit}", inline=False)

                embed_list.append(newEmbed)

            paginator: con.buttonHandler = await self.shared.callable(fun="buttonHandler", timeout=10 * 60)
            embed: discord.Embed = discord.Embed(title="Automod Rules", description="Server's Automod rules.\nUse arrows to navigate.", color=0x00ff2a, timestamp= await self.CONNECTOR.callable(fun="datetime"))

            await interaction.response.send_message(embed=embed, view=paginator.create_paginator(messages=embed_list))
            paginator.original_message = await interaction.original_response()

        else:
            await interaction.response.send_message("You do not have permissions to execute this command.", ephemeral=True)

    @app_commands.choices(pre_sets=[
        app_commands.Choice(name="Profanity", value="profanity"),
        app_commands.Choice(name="Slurs", value="slurs"),
        app_commands.Choice(name="Sexual Content", value="sexual content"),
        ])
    @app_commands.command(name = "create_response", description = "Creates responses and uses them on automod trigger.")
    async def save(self, interaction: discord.Interaction, rule_id: str, response: str, trigger: str, pre_sets: app_commands.Choice[str] | None = None) -> None:
        BotData, ServerData = await self.database.load_data(server_id=interaction.guild.id, serverData=True, botConfig=True)
        def create_db_path(id: str, single: bool = False, path: str | None = None) -> bool:
            try:
                ServerData["AutoMod"][id]
            except KeyError:
                ServerData["AutoMod"][id] = {} if single is False else None
                
            if path is not None:
                for x in path.split(","):
                    try:
                        ServerData["AutoMod"][id][x]
                    except KeyError:
                        ServerData["AutoMod"][id][x] = None

        if interaction.user.guild_permissions.administrator or interaction.user.id in [x for x in BotData["owners"]]:
            try:
                automod_rule: discord.AutoModRule = await interaction.guild.fetch_automod_rule(int(rule_id))
            except:
                return await interaction.response.send_message(content="Invalid Automod rule ID provided.", ephemeral=True)
            
            automod_trigger: discord.AutoModTrigger = automod_rule.trigger
            
            #non editable rules (spam etc)
            if trigger == "/" and pre_sets is None and automod_trigger.type != discord.AutoModRuleTriggerType.keyword:
                create_db_path(id=rule_id, single=True)
                ServerData["AutoMod"][rule_id] = response

                self.database.save_data(server_id=interaction.guild.id, update_data=ServerData)
                
                await interaction.response.send_message(content=f"Successfully set `{response}` as response on rule trigger: **{automod_rule.name} ({rule_id})**")

            #keyword trigger
            elif pre_sets is None and automod_trigger.type == discord.AutoModRuleTriggerType.keyword:
                if trigger == "/":
                    create_db_path(id=rule_id, path="GLOBAL_VALUE")
                    ServerData["AutoMod"][rule_id]["GLOBAL_VALUE"] = response
                else:
                    create_db_path(id=rule_id, path=trigger)
                    for x in trigger.split(","):
                        ServerData["AutoMod"][rule_id][x] = response

                self.database.save_data(server_id=interaction.guild.id, update_data=ServerData)

                await interaction.response.send_message(content=f"Successfully set `{response}` as response on rule trigger: **{automod_rule.name} ({rule_id})**; Keywords: `{trigger if trigger != '/' else 'GLOBAL_VALUE'}`")

            #presets
            elif pre_sets is not None and automod_trigger.type == discord.AutoModRuleTriggerType.keyword_preset:
                create_db_path(id=rule_id, path=pre_sets.value)
                ServerData["AutoMod"][rule_id][pre_sets.value] = response

                self.database.save_data(server_id=interaction.guild.id, update_data=ServerData)
    
                await interaction.response.send_message(content=f"Successfully set `{response}` as response on rule trigger: **{automod_rule.name} ({rule_id})**; Pre-set: `{pre_sets.name}`")
            else:
                await interaction.response.send_message(content="No match found. Please change parameters.", ephemeral=True)
            
        else:
            await interaction.response.send_message(content="You do not have permissions to execute this command.", ephemeral=True)

async def setup(bot: commands.Bot) -> None:
    pass
    #await bot.add_cog(AutomodCommand())
