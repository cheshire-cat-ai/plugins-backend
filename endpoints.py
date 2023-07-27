from fastapi import HTTPException, APIRouter
import httpx
from datetime import datetime
from utils import is_cache_valid, fetch_plugin_json


class Endpoints:

    def __init__(self, app, json, cache_duration, page_size):
        self.cache_duration = cache_duration
        self.json = json
        self.page_size = page_size
        self.app = app
        self.cache = {}
        self.cache_timestamp = {}
        # Define FastAPI endpoints
        self.router = APIRouter()
        self.router.add_api_route("/plugins", self.read_remote_json, methods=["GET"])
        self.router.add_api_route("/tags", self.get_all_tags, methods=["GET"])
        self.router.add_api_route("/tag/{tag_name}", self.get_plugins_by_tag, methods=["GET"])
        app.include_router(self.router)

    async def read_remote_json(self, page: int = 1, page_size: int = 0):
        if page_size == 0:
            page_size = self.page_size

        # Check if cache is still valid
        if is_cache_valid(self.cache_duration, self.cache_timestamp):
            cached_plugins = self.cache["plugins"]
        else:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(self.json)
                    data = response.json()

                    total_plugins = len(data)
                    start_index = (page - 1) * page_size
                    end_index = start_index + page_size

                    if start_index >= total_plugins:
                        return []

                    cached_plugins = []
                    for entry in data[start_index:end_index]:
                        url = entry["url"]
                        plugin_json_url = url.replace("github.com", "raw.githubusercontent.com") + "/main/plugin.json"
                        try:
                            plugin_data = await fetch_plugin_json(plugin_json_url)
                            cached_plugins.append(plugin_data)
                        except httpx.RequestError as e:
                            error_msg = f"Error fetching plugin.json for URL: {plugin_json_url}, Error: {str(e)}"
                            cached_plugins.append({"error": error_msg})

                    # Update the cache with the new data and timestamp
                    self.cache["plugins"] = cached_plugins
                    self.cache_timestamp["plugins"] = datetime.utcnow()

            except httpx.RequestError as e:
                raise HTTPException(status_code=500, detail=f"Error fetching GitHub data: {str(e)}")

        return {
            "total_plugins": len(cached_plugins),
            "page": page,
            "page_size": page_size,
            "plugins": cached_plugins,
        }

    async def get_all_tags(self):
        # Check if cache is still valid, otherwise update the cache
        if not is_cache_valid(self.cache_duration, self.cache_timestamp):
            await self.read_remote_json()

        # Get all tags from plugin data
        all_tags = set()
        for plugin_data in self.cache["plugins"]:
            if "tags" in plugin_data:
                tags = plugin_data["tags"]
                if isinstance(tags, str):
                    all_tags.add(tags)
                elif isinstance(tags, list):
                    all_tags.update(tags)

        return list(all_tags)

    async def get_plugins_by_tag(self, tag_name: str, page: int = 1, page_size: int = 0):
        if page_size == 0:
            page_size = self.page_size

        # Check if cache is still valid, otherwise update the cache
        if not is_cache_valid(self.cache_duration, self.cache_timestamp):
            await self.read_remote_json()

        # Find plugins containing the given tag
        matching_plugins = [plugin_data for plugin_data in self.cache["plugins"] if "tags" in plugin_data and tag_name in plugin_data["tags"]]

        total_plugins = len(matching_plugins)
        start_index = (page - 1) * page_size
        end_index = start_index + page_size

        if start_index >= total_plugins:
            return []

        return {
            "total_plugins": total_plugins,
            "page": page,
            "page_size": page_size,
            "plugins": matching_plugins[start_index:end_index],
        }
