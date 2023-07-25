import httpx
from fastapi import FastAPI, HTTPException, Query
from datetime import datetime, timedelta

app = FastAPI()

GITHUB_PLUGINS_JSON_URL = "https://raw.githubusercontent.com/cheshire-cat-ai/awesome-plugins/main/plugins.json"
DEFAULT_PAGE_SIZE = 10
CACHE_DURATION_MINUTES = 1440  # Set cache duration (1 day in minutes)


async def fetch_plugin_json(url):
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()


# Dictionary to store cached plugin.json data
cache = {}
cache_timestamp = {}


def is_cache_valid():
    """
    Check if the cache is still valid based on the cache duration.
    """
    if "plugins" not in cache_timestamp:
        return False
    cache_time = cache_timestamp["plugins"]
    return datetime.utcnow() < cache_time + timedelta(minutes=CACHE_DURATION_MINUTES)


@app.get("/plugins")
async def read_remote_json(page: int = 1, page_size: int = DEFAULT_PAGE_SIZE):
    global cache, cache_timestamp

    # Check if cache is still valid
    if is_cache_valid():
        cached_plugins = cache["plugins"]
    else:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(GITHUB_PLUGINS_JSON_URL)
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
                cache["plugins"] = cached_plugins
                cache_timestamp["plugins"] = datetime.utcnow()

        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Error fetching GitHub data: {str(e)}")

    return {
        "total_plugins": len(cached_plugins),
        "page": page,
        "page_size": page_size,
        "plugins": cached_plugins,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
