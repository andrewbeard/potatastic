import logging

import aiomqtt
import anyio
from asphalt.core import Component, current_context
from meshage.config import MQTTConfig
from meshage.messages import MeshtasticNodeInfoMessage, MeshtasticTextMessage
from meshage.parser import MeshtasticMessageParser

from .NewSpotEventSource import NewSpotEventSource
from .ReceivedMessageEventSource import ReceivedMessageEventSource
from .Spot import Spot


class MeshtasticCommunicationComponent(Component):
    def __init__(self):
        self.task_group = None
        self.running = False

    async def start(self, ctx) -> None:
        ctx.add_resource(MQTTConfig())
        ctx.add_resource(ReceivedMessageEventSource(), name="received_message_event_source")

        self.task_group = anyio.create_task_group()
        await self.task_group.__aenter__()
        self.running = True
        self.task_group.start_soon(self.publish_task)
        self.task_group.start_soon(self.receive_task)

    async def stop(self) -> None:
        self.running = False
        if self.task_group:
            await self.task_group.__aexit__(None, None, None)

    async def publish_task(self) -> None:
        logging.info("Starting publish task")
        event_source = await current_context().request_resource(
            NewSpotEventSource, "new_spot_event_source"
        )
        assert event_source is not None
        logging.debug(f"Event source: {event_source}")

        config = await current_context().request_resource(MQTTConfig)
        assert config is not None
        logging.debug(f"Config: {config.config}")

        logging.debug(f"Publish connecting to {config.config["host"]}")
        async with aiomqtt.Client(**config.aiomqtt_config) as broker:
            logging.debug(f"Publish connected to broker")
            node_info = MeshtasticNodeInfoMessage(config)
            try:
                await broker.publish(config.publish_topic, payload=bytes(node_info))
                logging.debug("Published node info")
            except Exception:
                logging.exception(f"Error publishing node info")
            else:
                logging.debug("Published node info")

            try:
                logging.debug("Waiting for spot events")

                async for event in event_source.signal.stream_events():
                    logging.debug(f"Publishing new spot: {event.spot.key}")
                    message = MeshtasticTextMessage(str(event.spot), config)
                    await broker.publish(config.publish_topic, payload=bytes(message))
            except Exception:
                logging.exception(f"Error in publish task")


    async def receive_task(self) -> None:
        logging.info("Starting receive task")
        config = await current_context().request_resource(MQTTConfig)
        assert config is not None

        received_message_event_source = await current_context().request_resource(ReceivedMessageEventSource, "received_message_event_source")
        assert received_message_event_source is not None

        logging.debug(f"Receive connecting to {config.config["host"]}")
        async with aiomqtt.Client(**config.aiomqtt_config) as broker:
            parser = MeshtasticMessageParser(config)
            logging.debug(f"Receive connected to broker")
            await broker.subscribe(config.receive_topic)
            logging.debug("Subscribed to receive topic")
            async for message in broker.messages:
                parsed_message = parser.parse_message(message.payload)
                if isinstance(parsed_message, MeshtasticTextMessage):
                    logging.info(f"Received text message: {parsed_message.text}")
                if parsed_message:
                    received_message_event_source.signal.dispatch(parsed_message)
