import sys, uuid, typing, platform, aiohttp, asyncio, schedule
sys.dont_write_bytecode = True
from discord.ext import commands
from src.core.root.event import Event

class Shared:
    bot: commands.Bot = None
    path: str = None
    OS: str = platform.system()
    session: aiohttp.ClientSession = None
    schedule_jobs: list[schedule.Job] = []
    
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
        from src.core.helpers.images import Images
        from src.core.helpers.string_formats import StringFormats
        from src.core.helpers.time import TimeHelper
        from src.core.helpers.errors import ErrorHelper

        self.images = Images()
        self.string_formats = StringFormats()
        self.time = TimeHelper()
        self.errors = ErrorHelper()

        from src.core.plugins.impersonator_detection import ImpersonatorDetection
        from src.core.plugins.AI import AI
        from src.core.plugins.ping_protection import PingProtection
        from src.core.plugins.auto_slowmode import AutoSlowmode
        from src.core.plugins.message_handlers import MessageHandlers
        from src.core.plugins.QOFTD import QOFTD
        from src.core.plugins.auto_deleter import AutoDeleter
        from src.core.plugins.miscellaneous_handlers import MiscellaneousHandlers
        from src.core.plugins.reaction_filter import ReactionFilter

        self.imper_detection = ImpersonatorDetection()
        self.AI = AI()    
        self.ping_prot = PingProtection()
        self.message_handlers = MessageHandlers()
        self.auto_deleter = AutoDeleter()
        self.QOFTD = QOFTD()
        self.auto_slowmode = AutoSlowmode()
        self.miscellaneous = MiscellaneousHandlers()
        self.reaction_filter = ReactionFilter()

        loader: tuple[typing.Callable] = (self.auto_slowmode.start, self.QOFTD.start, self.auto_deleter.start, self.reaction_filter.start, self.sender.start)
        self.plugin_tasks: list[asyncio.Task] = [self.loop.create_task(func(), name=func.__qualname__) for func in loader]

        self.queue.reload_filters()

    def _create_id(self) -> str:
        return str(uuid.uuid4())

#making global class var, so data is presistent
shared: Shared = Shared()
