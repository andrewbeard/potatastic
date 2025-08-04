import logging

import aiomqtt
import anyio
from asphalt.core import Component, current_context
from meshage.config import MQTTConfig
from meshage.messages import MeshtasticNodeInfoMessage, MeshtasticTextMessage

from NewSpotEventSource import NewSpotEventSource
from Spot import Spot


async def publish_task() -> None:
    new_spots = await current_context().request_resource(list[Spot], "new_spots")
    assert new_spots is not None

    event_source = await current_context().request_resource(
        NewSpotEventSource, "new_spot_event_source"
    )
    assert event_source is not None

    config = await current_context().request_resource(MQTTConfig)
    assert config is not None

    async with aiomqtt.Client(**config.aiomqtt_config) as broker:
        node_info = MeshtasticNodeInfoMessage(config)
        try:
            await broker.publish(config.topic, payload=bytes(node_info))
        except Exception as e:
            logging.error(f"Error publishing node info: {e}")
        else:
            logging.debug("Published node info")

        while True:
            await event_source.signal.wait_event()
            logging.debug(f"Publishing {len(new_spots)} new spots")
            for spot in new_spots:
                message = MeshtasticTextMessage(str(spot), config)
                await broker.publish(config.topic, payload=bytes(message))


class MeshtasticConsumerComponent(Component):
    def __init__(self):
        self.task_group = None
        self.running = False

    async def start(self, ctx) -> None:
        ctx.add_resource(MQTTConfig())

        self.task_group = anyio.create_task_group()
        await self.task_group.__aenter__()
        self.running = True
        self.task_group.start_soon(publish_task)

    async def stop(self) -> None:
        self.running = False
        if self.task_group:
            await self.task_group.__aexit__(None, None, None)
