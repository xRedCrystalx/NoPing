import sys, discord
sys.dont_write_bytecode = True
from src.connector import shared

from xRedUtils.type_hints import SIMPLE_ANY

class Responder:
    async def respond(self, message: discord.Message, guild_db: dict[str, SIMPLE_ANY], **OVERFLOW) -> None:
        if guild_db["responder"]["status"]:
            # check every phrase in the db
            for phrase, data in guild_db["responder"]["responses"].items():
                if data["startsWith"]:
                    if message.content.startswith(phrase):
                        await message.channel.send(data["content"])
                else:
                    if phrase in message.content:
                        await message.channel.send(data["content"])
        return None

async def setup(bot) -> None:
    pass
    #await con.shared.plugin_load(responder := Responder(), callable=(["on_message"], responder.respond))