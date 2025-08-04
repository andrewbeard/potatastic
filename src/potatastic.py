#! /usr/bin/env python3
import logging

from asphalt.core import ContainerComponent, run_application

from MeshtasticConsumerComponent import MeshtasticConsumerComponent
from ScraperComponent import ScraperComponent


def main():
    logging.basicConfig(
        format="%(asctime)s %(levelname)s:%(message)s", level=logging.INFO
    )
    # Start all components using ContainerComponent
    run_application(
        ContainerComponent(
            {
                "scraper": {"type": ScraperComponent},
                "consumer": {"type": MeshtasticConsumerComponent},
            }
        )
    )


if __name__ == "__main__":
    main()
