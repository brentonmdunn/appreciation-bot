# Appreciation Bot

Discord bot used for managing AACF appreciation banquets.

## Development

Clone repository:
```
$ git clone https://github.com/brentonmdunn/appreciation-bot.git
```

Go to Discord developer portal and create a new bot. Add `.env` file in the root directory with the token from Discord:
```
TOKEN=<your token>
```

(Optional but recommended) Create virtual environment:
```
$ python -m venv .venv
```

Install dependecies:
```
$ pip install -r requirements.txt
```

## Deployment

The bot can be run on your server using Docker. This bot can be found on [DockerHub](https://hub.docker.com/r/brentonmdunn/appreciation-bot).

Command to push to DockerHub:

```
$ docker buildx build --platform linux/amd64,linux/arm64 -t brentonmdunn/appreciation-bot --push .
```