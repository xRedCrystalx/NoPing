import sys, typing, asyncio
sys.dont_write_bytecode = True
import src.connector as con

from src.core.helpers.errors import report_error, full_traceback

class QueueSystem:
    def __init__(self) -> None:
        self.shared: con.Shared = con.shared

    # main event runner
    async def _thread_event_runner(self, funcs: tuple[typing.Callable], guild_id: int, **kwargs) -> None:        
        bot_database: dict[str, typing.Any] = self.shared.db.load_data()
        # if blacklisted
        if guild_id in bot_database["blacklisted_guilds"]:
            return

        guild_database: dict = self.shared.db.load_data(guild_id)
        # if turned off
        if not guild_database["general"]["status"]:
            return

        #if not fully configured
        if not (guild_database["general"]["staffRole"] and 
                guild_database["general"]["staffChannel"] and 
                guild_database["general"]["adminRole"] and 
                guild_database["general"]["adminChannel"]):
            return

        self.shared.logger.log(f"@QueueSystem._thread_event_runner > Recieved task for execution. Loaded guild's and bot's database into the memory.", "NP_DEBUG")

        try:
            tasks: list[asyncio.Task] = [self.shared.loop.create_task(func(guild_id=guild_id, guild_db=guild_database, bot_db=bot_database, **kwargs), name=func.__qualname__) for func in funcs]
            self.shared.logger.log(f"@QueueSystem._thread_event_runner > Created list of task functions.", "NP_DEBUG")
            
            done: set[asyncio.Task]
            pending: set[asyncio.Task]
            done, pending = await asyncio.wait(tasks, timeout=2.5)

            self.shared.logger.log(f"@QueueSystem._thread_event_runner > Execution completed. Returning completed and incompleted functions.", "NP_DEBUG")

            for task in [*done, *pending]:
                if not task.done():
                    task.cancel("Forcefully cancelled task.")
                    await asyncio.sleep(0)
                try:
                    result: list[dict] = await task
                    if result:
                        self.shared.sender.resolver(result)

                except (asyncio.CancelledError, asyncio.InvalidStateError, asyncio.TimeoutError):
                    self.shared.logger.log(f"@QueueSystem.Task.{task.get_name()} ({guild_id}): Task killed.", "WARNING")
                except Exception as error:
                    self.shared.logger.log(f"@QueueSystem.Task.{task.get_name()} ({guild_id}): {full_traceback()}", "ERROR")

            self.shared.logger.log(f"@QueueSystem._thread_event_runner > Completed main Task. Success rate: {len(done)}/{len(pending)+len(done)}", "NP_DEBUG")

        except ExceptionGroup as groupError:
            self.shared.logger.log(f"@QueueSystem._thread_event_runner ({guild_id}): Exception Group: {', '.join([f'SubE {num}: {exception}' for num, exception in enumerate(groupError.exceptions, 1)])}", "ERROR")
        except Exception as error:
            self.shared.logger.log(f"@QueueSystem._thread_event_runner ({guild_id}): {type(error).__name__}: {error}", "ERROR")
    
    # main queue adder
    async def add_to_queue(self, event: str, guild_id: int, **kwargs) -> None:
        self.shared.logger.log(f"@QueueSystem.add_to_queue > Recieved {event} event.", "NP_DEBUG")
        functions: tuple[typing.Callable] | None = self.filter.get(event)

        if functions:
            try:
                self.shared.loop.create_task(self._thread_event_runner(guild_id=guild_id, funcs=functions, **kwargs))
            except Exception as error:
                report_error(error, self.add_to_queue, "simple")
        return None

    # filter reloader
    def reload_filters(self) -> None:
        self.filter: dict[str, tuple[typing.Callable]] = {
            "on_message": (self.shared.AI.ask_ai, self.shared.ping_prot.find_pings, self.shared.auto_slowmode.message_listener,
                            self.shared.message_handlers.responder, self.shared.message_handlers.simon_invite_link_detection, self.shared.message_handlers.antilink,
                            self.shared.auto_deleter.add_to_queue, self.shared.hacked_accs.check_hacked),
            "on_message_edit": (self.shared.ping_prot.find_pings, self.shared.message_handlers.antilink, self.shared.message_handlers.simon_invite_link_detection),
            "on_automod_action": (self.shared.miscellaneous.automod_response, self.shared.hacked_accs.check_hacked),
            "on_member_join": (self.shared.imper_detection.detection_on_join,self.shared.miscellaneous.alt_detection),
            "on_member_update": (self.shared.imper_detection.detection_on_update, ),
            "on_raw_reaction_add": (self.shared.reaction_filter.check_reaction, ),
            "on_voice_state_update": ()
        }
        self.shared.logger.log(f"@QueueSystem.reload_filters > Filters reloaded.", "NP_DEBUG")
