import discord, asyncio, sys, typing
sys.dont_write_bytecode = True
import src.connector as con

if typing.TYPE_CHECKING:
    from discord.ext import commands

class AutoSlowmode:
    def __init__(self, interval_minutes: int = 5) -> None:
        self.shared: con.Shared = con.shared
        self.bot: commands.Bot = self.shared.bot

        self.slowmode_rules: dict[int, tuple[int, int]] = {
            5: (15, 60),
            10: (60, 130),
            15: (130, 250),
            20: (250, 400),
            30: (400, 750)
        }
        self.interval_minutes: int = interval_minutes
        self.database: dict = {}

    async def message_listener(self, message: discord.Message, guild_db: dict[str, typing.Any], **OVERFLOW) -> None:
        if str(message.channel.id) in guild_db["auto_slowmode"]["monitored"] and guild_db["auto_slowmode"]["status"]:
            self.shared.logger.log(f"@AutoSlowmode.message_listener > Recieved new event..", "NP_DEBUG")
            
            if self.database.get(message.channel.id):
                self.database[message.channel.id] += 1
                
                if message.channel.slowmode_delay <= 10:
                    if self.database[message.channel.id] > 100:
                        self.shared.logger.log(f"@AutoSlowmode.message_listener > Forcing slowmode. > 100 messages.", "NP_DEBUG")
                        await self.slowmode(channel=message.channel)
            else:
                self.database[message.channel.id] = 1

    async def slowmode(self, channel: discord.TextChannel) -> None:
        self.shared.logger.log(f"@AutoSlowmode.slowmode > Checking {channel.guild.name}: {channel.name} ({channel.id}).", "NP_DEBUG")
        guild_db: dict = self.shared.db.load_data(channel.guild.id)
        default_delay: int = guild_db["auto_slowmode"]["monitored"][str(channel.id)]
        
        numMsg: int | float = (self.database[channel.id] / 5) * channel.slowmode_delay
        total: int | float = numMsg - (numMsg * 20 / 100)
        self.shared.logger.log(f"@AutoSlowmode.slowmode > Message count: {total}.", "NP_DEBUG")

        for time, (smaller, bigger) in self.slowmode_rules.items():
            if total >= smaller and total < bigger:
                delay: int = time
                self.shared.logger.log(f"@AutoSlowmode.slowmode > Set delay: {delay}.", "NP_DEBUG")
                break
        else:
            if total < 15:
                delay = default_delay
            else:
                delay = 60

        self.shared.logger.log(f"@AutoSlowmode.slowmode > Got delay: {delay}.", "NP_DEBUG")


        if channel.slowmode_delay != delay and delay >= default_delay and guild_db["auto_slowmode"]["status"]:
            await self.shared.sender.resolver([{channel : {"action" : "edit", "kwargs" : {"slowmode_delay" : delay}}}])
            self.shared.logger.log(f"@AutoSlowmode.slowmode > Delay sent to the resolver.", "NP_DEBUG")
                
            if (channel_id := guild_db["auto_slowmode"]["log_channel"]):
                embed: discord.Embed = discord.Embed(title="Auto Slowmode", color=discord.Colour.dark_embed(), timestamp=self.shared._datetime())
                embed.add_field(name="`` Channel ``", value=f"<:text_c:1203423388320669716>┇{channel.name}\n<:ID:1203410054016139335>┇{channel.id}", inline=True)
                embed.add_field(name="`` Change ``", value=f"Value change:\n`{channel.slowmode_delay}s` ➔ `{delay}s`", inline=True)

                if channel := self.bot.get_channel(channel_id):
                    self.shared.logger.log(f"@AutoSlowmode.slowmode > Sending notification message.", "NP_DEBUG")
                    await self.shared.sender.resolver([{channel: {"action" : "send", "kwargs" : {"embed" : embed}}}])

    async def start(self) -> None:
        while True:
            await asyncio.sleep(self.interval_minutes * 60)
            self.shared.logger.log(f"@AutoSlowmode.start > Executing {self.interval_minutes} min loop.", "NP_DEBUG")

            for channel_id in self.database:
                channel: discord.TextChannel = self.bot.get_channel(channel_id)
                await self.slowmode(channel=channel)

            self.database.clear()
