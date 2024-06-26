import sys, typing, aiohttp, asyncio, schedule, re
sys.dont_write_bytecode = True
from discord.ext import commands
from xRedUtils import (system, 
                       typehints as th)

class Shared:
    bot: commands.Bot = None
    path: str = None
    OS: str = system.OS

    session: aiohttp.ClientSession = None
    schedule_jobs: list[schedule.Job] = []
    global_db: dict[th.SIMPLE_ANY, th.SIMPLE_ANY] = {
        "invite_links": {
            "regex": re.compile(r"(?:https?\:\/\/)?discord(?:\.gg|(?:app)?\.com\/invite)\/[^/]+", re.IGNORECASE),
            "simon": {},
            "scam_guilds": {}
        }
    }
    
    import src.system.colors as colors_module
    colors: colors_module.C | colors_module.CNone = colors_module.auto_color_handler()

    # system required
    def system_load(self) -> None:
        self.loop: asyncio.AbstractEventLoop = asyncio.get_running_loop()
        
        # system modules
        from src.system.database import Database
        from src.system.logging import Logger
        from src.system.reloader import Reloader

        self.db = Database()
        self.logger: Logger = Logger().main()
        self.reloader = Reloader()

        # main modules
        from src.core.transmitters.sender import Sender
        from src.core.transmitters.queue import QueueSystem

        self.sender = Sender()
        self.queue = QueueSystem()

        # security modules
        from src.core.root.execution_reports import ExecReport

        self.execution_reports = ExecReport()

    def plugin_load(self) -> None:        
        from src.core.helpers.string_formats import StringFormats

        self.string_formats = StringFormats()

        from src.core.plugins.impersonator_detection import ImpersonatorDetection
        from src.core.plugins.AI import AI
        from src.core.plugins.ping_protection import PingProtection
        from src.core.plugins.auto_slowmode import AutoSlowmode
        from src.core.plugins.message_handlers import MessageHandlers
        from src.core.plugins.QOFTD import QOFTD
        from src.core.plugins.auto_deleter import AutoDeleter
        from src.core.plugins.miscellaneous_handlers import MiscellaneousHandlers
        from src.core.plugins.reaction_filter import ReactionFilter
        from src.core.plugins.hacked_acc_detection import HackedAccounts

        self.imper_detection = ImpersonatorDetection()
        self.AI = AI()    
        self.ping_prot = PingProtection()
        self.message_handlers = MessageHandlers()
        self.auto_deleter = AutoDeleter()
        self.QOFTD = QOFTD()
        self.auto_slowmode = AutoSlowmode()
        self.miscellaneous = MiscellaneousHandlers()
        self.reaction_filter = ReactionFilter()
        self.hacked_accs = HackedAccounts()

        loader: tuple[typing.Callable] = (self.auto_slowmode.start, self.QOFTD.start, self.auto_deleter.start, self.reaction_filter.start, self.sender.start)
        self.plugin_tasks: list[asyncio.Task] = [self.loop.create_task(func(), name=func.__qualname__) for func in loader]

        self.queue.reload_filters()

#making global class var, so data is presistent
shared: Shared = Shared()
