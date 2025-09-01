import logging

import anyio
from asphalt.core import Component, current_context

from .CommandEventSource import CommandEventSource
from .State import State

class CommandProcessorComponent(Component):
    def __init__(self):
        self.task_group = None
        self.running = False

    async def start(self, ctx) -> None:
        ctx.add_resource(State)
        self.task_group = anyio.create_task_group()
        await self.task_group.__aenter__()
        self.running = True
        self.task_group.start_soon(self.task)

    async def stop(self) -> None:
        self.running = False
        if self.task_group:
            await self.task_group.__aexit__(None, None, None)

    async def task(self) -> None:
        logging.info("Starting command processor task")
        event_source = await current_context().request_resource(
            CommandEventSource, "command_event_source"
        )
        assert event_source is not None

        async for event in event_source.signal.stream_events():
            logging.info(f"Received command: {event.command} from {event.userId}")
            await self.parse_command(event.command)

    async def parse_command(self, command: str) -> None:
        state = await current_context().request_resource(State)
        assert state is not None

        parts = command.split()
        if parts[0] == "enable":
            state.enabled = True
            logging.info("Publishing enabled")
        elif parts[0] == "disable":
            state.enabled = False
            logging.info("Publishing enabled")
        else:
            logging.warning(f"Unknown command: {command}")
