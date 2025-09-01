import logging

import anyio
import requests
from asphalt.core import Component, current_context

from .NewSpotEventSource import NewSpotEventSource
from .Spot import Spot
from .State import State


class ScraperComponent(Component):
    SPOT_URL = "https://api.pota.app/v1/spots"
    FETCH_PERIOD = 30

    def __init__(self):
        self.task_group = None
        self.running = False

    async def start(self, ctx) -> None:
        ctx.add_resource(NewSpotEventSource(), name="new_spot_event_source")
        ctx.add_resource({}, name="spots", types=dict[str, Spot])

        self.task_group = anyio.create_task_group()
        await self.task_group.__aenter__()
        self.running = True
        self.task_group.start_soon(self.task)

    async def stop(self) -> None:
        self.running = False
        if self.task_group:
            await self.task_group.__aexit__(None, None, None)

    def get_spot_reports(self) -> list[Spot]:
        return [Spot(spot) for spot in requests.get(self.SPOT_URL).json()]

    def get_new_spots(self, spots: dict[str, Spot], scrape: list[Spot]) -> list[Spot]:
        added = []
        for new_spot in scrape:
            if new_spot.key not in spots:
                # Must be a new one
                spots[new_spot.key] = new_spot
                added.append(new_spot)
                logging.debug(f"New spot: {new_spot.key}")
        return added

    async def task(self) -> None:
        logging.info("Starting scraper task")
        new_spot_event_source = await current_context().request_resource(
            NewSpotEventSource, "new_spot_event_source"
        )
        assert new_spot_event_source is not None
        spots = await current_context().request_resource(dict[str, Spot], "spots")
        assert spots is not None
        #state = await current_context().request_resource(State)
        #assert state is not None

        while self.running:
            try:
                logging.debug("Fetching spot reports...")
                scrape = self.get_spot_reports()
                added = self.get_new_spots(spots, scrape)
                logging.info(f"Retrieved {len(scrape)} spot reports, {len(added)} new")

                for spot in scrape:
                    spots[spot.key] = spot

                if True or state.enabled:
                    for spot in added:
                        await new_spot_event_source.signal.dispatch(spot)

            except Exception:
                logging.exception(f"Error fetching spot reports")
            finally:
                await anyio.sleep(self.FETCH_PERIOD)

