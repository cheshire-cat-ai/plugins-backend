import os
from fastapi import FastAPI
import uvicorn
from endpoints import Endpoints

GITHUB_PLUGINS_JSON_URL = os.getenv("GITHUB_PLUGINS_JSON_URL", "https://raw.githubusercontent.com/cheshire-cat-ai/awesome-plugins/main/plugins.json")
DEFAULT_PAGE_SIZE = int(os.getenv("DEFAULT_PAGE_SIZE",10))
CACHE_DURATION_MINUTES = int(os.getenv("CACHE_DURATION_MINUTES",1440))
RELOAD = bool(os.getenv("RELOAD", True))

app = FastAPI()

backend = Endpoints(app=app, json=GITHUB_PLUGINS_JSON_URL, page_size=DEFAULT_PAGE_SIZE, cache_duration=CACHE_DURATION_MINUTES)

host = os.environ["HOST"]
port = int(os.environ["PORT"])

if __name__ == "__main__":
    uvicorn.run("main:app", host=host, port=port, reload=RELOAD)
