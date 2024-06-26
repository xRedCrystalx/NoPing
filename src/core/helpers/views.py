import sys, discord
sys.dont_write_bytecode = True
import src.connector as con
from discord.ui import View

from .errors import report_error

class ViewHelper(View):
    def __init__(self, timeout: float | None = 60) -> None:
        super().__init__(timeout=timeout)
        
        self.shared: con.Shared = con.shared
        self.interaction: discord.Interaction = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        self.interaction = interaction
        return await super().interaction_check(interaction)
    
    async def on_timeout(self) -> None:
        self.stop()
        try:
            original_message: discord.InteractionMessage = await self.interaction.original_response()
            await original_message.edit(view=None)
        # message doesn't exist/can't fetch
        except: pass
    
    async def on_error(self, interaction: discord.Interaction, error: Exception, item) -> None:
        error_id: str = report_error(error, self.on_error, "simple")
        await interaction.response.send_message(f"**An error has occured. Report this to the developer.**\n**Error ID:** `{error_id}`")
