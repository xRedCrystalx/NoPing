import discord, sys
sys.dont_write_bytecode = True
from .errors import report_error

class ModalHelper(discord.ui.Modal):
    def __init__(self, title: str, custom_id: str, timeout: float | None = None) -> None:
        """
        Handler for `discord.Modal`
        
        - my_modal.get_data()     [`dict` | `None`] -> get original dict of returned data or error
        or
        - my_modal.clean_data()   [`dict` | `None`] -> get filtered/clean dict of returned data or error
        """
        
        super().__init__(title=title, timeout=timeout, custom_id=custom_id)
        
        self.data: None | dict = None
        self.interaction: discord.Interaction = None
    
    async def on_submit(self, interaction: discord.Interaction) -> None:
        self.data = dict(interaction.data) | {"interaction": interaction}

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await report_error(f"ModalHelper.on_error<{interaction.data["custom_id"]}>", "full")
        self.data = {"error": error, "interaction": interaction}

    async def on_timeout(self) -> None:
        self.data = {"error": "Timed out."}
        self.stop()

    async def get_data(self) -> dict[str, str | list[dict] | Exception | discord.Interaction] | None:
        """Returns raw data (discord response)"""
        await self.wait()
        return self.data
    
    async def clean_data(self) -> dict[str, str | dict[str, str] | Exception] | None:
        raw: dict[str, str | list[dict]] = await self.get_data()
        if not raw or raw.get("error"):
            return raw
    
        return {"modal_id": raw.get("custom_id"), "interaction": raw.get("interaction"),
                "components": {item["components"][0].get("custom_id"): item["components"][0].get("value") for item in raw.get("components")}}
