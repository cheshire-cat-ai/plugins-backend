import os
from fastapi import FastAPI
import uvicorn
from endpoints import Endpoints

GITHUB_PLUGINS_JSON_URL = os.environ["GITHUB_PLUGINS_JSON_URL"]
DEFAULT_PAGE_SIZE = int(os.environ["DEFAULT_PAGE_SIZE"])
CACHE_DURATION_MINUTES = int(os.environ["CACHE_DURATION_MINUTES"])
RELOAD = bool(os.environ["RELOAD"])

app = FastAPI()

backend = Endpoints(app=app, json=GITHUB_PLUGINS_JSON_URL, page_size=DEFAULT_PAGE_SIZE, cache_duration=CACHE_DURATION_MINUTES)

host = os.environ["HOST"]
port = int(os.environ["PORT"])

if __name__ == "__main__":
    uvicorn.run("main:app", host=host, port=port, reload=RELOAD)
