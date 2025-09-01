#! /usr/bin/env python3
import logging

from asphalt.core import ContainerComponent, run_application

from .CommandProcessorComponent import CommandProcessorComponent
from .MeshtasticCommunicationComponent import MeshtasticCommunicationComponent
from .ScraperComponent import ScraperComponent


def main():
    logging.basicConfig(
        format="%(asctime)s %(levelname)s:%(message)s", level=logging.DEBUG
    )
    # Start all components using ContainerComponent
    run_application(
        ContainerComponent(
            {
                "scraper": {"type": ScraperComponent},
                "mqtt": {"type": MeshtasticCommunicationComponent},
                "commands": {"type": CommandProcessorComponent},
            }
        )
    )


if __name__ == "__main__":
    main()
