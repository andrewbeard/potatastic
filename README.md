# POTAtastic

Publishes POTA spots to Meshtastic via MQTT. This application uses the meshage library for [Meshtastic](https://github.com/andrewbeard/meshage) message parsing.

## Getting Started

- Set up an MQTT server accessible from where potatastic will be run and from the node that will be publishing messages to the mesh
- Create a channel and note the name and encryption key
- Configure your publishing node to use your MQTT server for bridging messages.
- Create an mqtt.conf file according to the meshage library, including the address and credentials of your MQTT server and the details of the channel you created.
- Start the [Docker image](https://hub.docker.com/r/bearda/potatastic), mounting the config file to /app/mqtt.c onf

