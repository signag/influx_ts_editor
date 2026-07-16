# Getting started with Influx TS Editor

[![Up](img/goup.gif)](./index.md)

## Requirements

- An instance of an [Influx DB V2](https://docs.influxdata.com/influxdb/v2/)    
([Influx DB V3](https://docs.influxdata.com/influxdb3/core/) is currently not yet supported)
- Either a PC or Linux system with Python 3 installed 
- or alternatively a Docker container manager on an arbitrary system, such as a NAS.    
When you are running InfluxDB in a Docker container, you may want to install *Influx TS Editor* on the same Docker instance.

---

## Installation

### Create Docker Container with Image from Docker Hub

Image: [https://hub.docker.com/repository/docker/signag/influx_ts_editor](https://hub.docker.com/repository/docker/signag/influx_ts_editor)

In an arbitrary working directory on the server hosting Docker, create 

```compose.yaml```

```yml
services:
  influx_ts_editor:
    image: signag/influx_ts_editor
    container_name: influx_ts_editor
    network_mode: "host"
    ports:
      - "5000:5000"
    volumes:
      - influx_ts_editor-data:/data
    environment:
      - SETTINGS_FILE=/data/settings.json
      - LOG_LEVEL=ERROR
    restart: unless-stopped
    privileged: true
    
volumes:
  influx_ts_editor-data:  
```

Adjust the ```ports``` mapping and ```LOG_LEVEL``` to your needs.

Connection settings (URL, organisation, optionally token) are stored in a named Docker volume
so they survive container restarts.

Then run

```
docker compose pull influx_ts_editor
docker compose create influx_ts_editor
docker compose start influx_ts_editor
```

From an arbitrarary browser, open           
**```http://<host>:5000```**    
replacing ```<host>``` with IP address or network name of your Docker host.

---

### Running locally (without Docker)

```bash
git clone https://github.com/signag/influx_ts_editor.git
cd influx_ts_editor
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

The app starts on **http://localhost:5000**.  
Settings are stored in `data/settings.json` (created automatically).



---

## Environment variables

| Variable       | Default                          | Description                          |
|----------------|----------------------------------|--------------------------------------|
| `SETTINGS_FILE`| `./data/settings.json`           | Path to the persisted settings file  |
| `PORT`         | `5000`                           | HTTP port the server listens on      |
| `LOG_LEVEL`    | `ERROR`                          | Python logging level                 |
| `DEBUG`        | `false`                          | Set to `true` for Flask debug mode   |

